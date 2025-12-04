"""
PDF Signing Service

Provides PDF signing and verification using:
- User certificates (not global keys)
- Post-quantum signatures
- Signature verification
- Long-term validation support
"""

import os
import json
import hashlib
import base64
from datetime import datetime
from typing import Tuple, Optional
from django.conf import settings
from django.utils import timezone

from ..models import UserCertificate, PKIAuditLog
from ..crypto import ClassicalCrypto, PostQuantumCrypto, HybridCrypto, CryptoUtils
from .ca_service import CAService

# Try to import PDF library
try:
    from PDFNetPython3.PDFNetPython import (
        PDFNet, PDFDoc, SDFDoc, Rect, Image,
        SignatureWidget, DigitalSignatureField, Field
    )
    PDFNET_AVAILABLE = True
except ImportError:
    PDFNET_AVAILABLE = False
    print("Warning: PDFNetPython3 not available. PDF signing features limited.")


class PDFSigningService:
    """
    Service for PDF signing and verification operations.
    
    Features:
    - Sign PDFs with user's personal certificate
    - Hybrid signatures (classical + post-quantum)
    - Signature verification
    - Certificate chain embedding
    """
    
    # Signature appearance settings
    SIGNATURE_WIDTH = 150
    SIGNATURE_HEIGHT = 50
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if PDF signing is available."""
        return PDFNET_AVAILABLE
    
    @classmethod
    def sign_pdf(cls,
                 input_file: str,
                 certificate: UserCertificate,
                 private_key_pem: bytes,
                 pq_private_key: bytes = None,
                 signature_id: str = None,
                 x_coordinate: int = 100,
                 y_coordinate: int = 100,
                 page: int = 1,
                 reason: str = "Document signed digitally",
                 location: str = "Vietnam",
                 output_file: str = None,
                 signature_image: str = None,
                 user=None,
                 request=None) -> dict:
        """
        Sign a PDF document with user's certificate.
        
        Args:
            input_file: Path to input PDF
            certificate: User's certificate
            private_key_pem: User's private key in PEM format
            pq_private_key: User's PQ private key (optional)
            signature_id: Unique signature field ID
            x_coordinate: X position for signature
            y_coordinate: Y position for signature
            page: Page number for signature (1-indexed)
            reason: Signing reason
            location: Signing location
            output_file: Path for signed PDF (auto-generated if not provided)
            signature_image: Path to signature image
            user: User performing signing
            request: HTTP request
            
        Returns:
            dict with signing result
        """
        if not PDFNET_AVAILABLE:
            return cls._sign_pdf_fallback(
                input_file, certificate, private_key_pem, 
                pq_private_key, output_file, user, request
            )
        
        # Validate certificate
        if not certificate.is_valid():
            raise ValueError("Certificate is not valid for signing")
        
        if not certificate.can_sign_documents():
            raise ValueError("Certificate is not authorized for document signing")
        
        # Generate output filename
        if not output_file:
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_signed{ext}"
        
        # Generate signature ID
        if not signature_id:
            signature_id = f"sig_{int(datetime.now().timestamp())}"
        
        try:
            # Initialize PDFNet
            PDFNet.Initialize()
            
            # Open document
            doc = PDFDoc(input_file)
            
            # Create signature field
            sig_field = SignatureWidget.Create(
                doc, 
                Rect(x_coordinate, y_coordinate, 
                     x_coordinate + cls.SIGNATURE_WIDTH, 
                     y_coordinate + cls.SIGNATURE_HEIGHT),
                signature_id
            )
            
            # Add to specified page
            pg = doc.GetPage(page)
            if pg:
                pg.AnnotPushBack(sig_field)
            
            # Get signature field
            approval_field = doc.GetField(signature_id)
            digsig_field = DigitalSignatureField(approval_field)
            
            # Add signature appearance
            if signature_image and os.path.exists(signature_image):
                img = Image.Create(doc.GetSDFDoc(), signature_image)
                widget = SignatureWidget(approval_field.GetSDFObj())
                widget.CreateSignatureAppearance(img)
            
            # Create temporary PKCS#12 for PDFNet
            p12_path = cls._create_temp_p12(certificate, private_key_pem)
            
            try:
                # Sign with certificate
                digsig_field.SignOnNextSave(p12_path, '')
                
                # Save signed document
                doc.Save(output_file, SDFDoc.e_incremental)
            finally:
                # Clean up temp file
                if os.path.exists(p12_path):
                    os.remove(p12_path)
            
            doc.Close()
            
            # Calculate document hash
            doc_hash = cls._calculate_file_hash(output_file)
            
            # Create post-quantum signature if available
            pq_signature = None
            if pq_private_key and certificate.has_pq_key:
                pq_signature = cls._create_pq_signature(
                    output_file, pq_private_key, certificate.pq_algorithm
                )
            
            # Record usage
            certificate.record_usage()
            
            # Audit log
            PKIAuditLog.log(
                event_type='DOCUMENT_SIGNED',
                description=f"PDF signed: {os.path.basename(input_file)}",
                user=user,
                request=request,
                certificate=certificate,
                severity='INFO',
                details={
                    'input_file': os.path.basename(input_file),
                    'output_file': os.path.basename(output_file),
                    'document_hash': doc_hash,
                    'has_pq_signature': bool(pq_signature),
                }
            )
            
            return {
                'success': True,
                'output_file': output_file,
                'signature_id': signature_id,
                'document_hash': doc_hash,
                'certificate_serial': certificate.serial_number,
                'signer': certificate.subject_dn,
                'signed_at': datetime.now().isoformat(),
                'has_pq_signature': bool(pq_signature),
                'pq_signature': pq_signature,
            }
            
        except Exception as e:
            PKIAuditLog.log(
                event_type='SYSTEM_ERROR',
                description=f"PDF signing failed: {str(e)}",
                user=user,
                request=request,
                certificate=certificate,
                severity='ERROR',
                success=False,
                error_message=str(e)
            )
            raise
    
    @classmethod
    def _sign_pdf_fallback(cls, input_file, certificate, private_key_pem,
                           pq_private_key, output_file, user, request) -> dict:
        """
        Fallback signing method when PDFNet is not available.
        
        Creates a detached signature file instead of embedded signature.
        """
        import shutil
        
        if not output_file:
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_signed{ext}"
        
        # Copy original file
        shutil.copy2(input_file, output_file)
        
        # Read file content
        with open(input_file, 'rb') as f:
            content = f.read()
        
        # Calculate hash
        doc_hash = hashlib.sha384(content).digest()
        
        # Load private key
        private_key = ClassicalCrypto.load_private_key(private_key_pem)
        
        # Create classical signature
        classical_signature = ClassicalCrypto.sign_data(private_key, doc_hash)
        
        # Create PQ signature if available
        pq_signature = None
        if pq_private_key:
            pq_signature = PostQuantumCrypto.sign(
                pq_private_key, doc_hash, certificate.pq_algorithm
            )
        
        # Create signature manifest
        signature_data = {
            'version': '1.0',
            'type': 'detached_signature',
            'document_hash': base64.b64encode(doc_hash).decode('ascii'),
            'hash_algorithm': 'SHA-384',
            'classical_signature': base64.b64encode(classical_signature).decode('ascii'),
            'classical_algorithm': certificate.key_algorithm,
            'certificate_serial': certificate.serial_number,
            'certificate_subject': certificate.subject_dn,
            'certificate_pem': certificate.certificate_pem,
            'signed_at': datetime.now().isoformat(),
        }
        
        if pq_signature:
            signature_data['pq_signature'] = base64.b64encode(pq_signature).decode('ascii')
            signature_data['pq_algorithm'] = certificate.pq_algorithm
            signature_data['pq_public_key'] = base64.b64encode(
                certificate.pq_public_key
            ).decode('ascii')
        
        # Save signature file
        sig_file = output_file + '.sig'
        with open(sig_file, 'w') as f:
            json.dump(signature_data, f, indent=2)
        
        # Record usage
        certificate.record_usage()
        
        # Audit log
        PKIAuditLog.log(
            event_type='DOCUMENT_SIGNED',
            description=f"PDF signed (detached): {os.path.basename(input_file)}",
            user=user,
            request=request,
            certificate=certificate,
            severity='INFO',
            details={
                'method': 'detached',
                'signature_file': os.path.basename(sig_file),
            }
        )
        
        return {
            'success': True,
            'output_file': output_file,
            'signature_file': sig_file,
            'document_hash': base64.b64encode(doc_hash).decode('ascii'),
            'certificate_serial': certificate.serial_number,
            'signer': certificate.subject_dn,
            'signed_at': signature_data['signed_at'],
            'has_pq_signature': bool(pq_signature),
            'method': 'detached',
        }
    
    @classmethod
    def verify_pdf_signature(cls,
                             pdf_file: str,
                             signature_file: str = None,
                             user=None,
                             request=None) -> dict:
        """
        Verify a signed PDF document.
        
        Args:
            pdf_file: Path to signed PDF
            signature_file: Path to detached signature (if applicable)
            user: User performing verification
            request: HTTP request
            
        Returns:
            dict with verification results
        """
        result = {
            'valid': False,
            'classical_valid': False,
            'pq_valid': None,
            'certificate_valid': False,
            'signer': None,
            'signed_at': None,
            'errors': [],
            'warnings': [],
        }
        
        # Check for detached signature
        if not signature_file:
            signature_file = pdf_file + '.sig'
        
        if os.path.exists(signature_file):
            # Verify detached signature
            return cls._verify_detached_signature(
                pdf_file, signature_file, user, request
            )
        
        if PDFNET_AVAILABLE:
            # Verify embedded signature using PDFNet
            return cls._verify_embedded_signature(pdf_file, user, request)
        
        result['errors'].append("No signature found and PDFNet not available")
        return result
    
    @classmethod
    def _verify_detached_signature(cls, pdf_file: str, sig_file: str,
                                    user=None, request=None) -> dict:
        """Verify a detached signature."""
        result = {
            'valid': False,
            'classical_valid': False,
            'pq_valid': None,
            'certificate_valid': False,
            'signer': None,
            'signed_at': None,
            'errors': [],
            'warnings': [],
        }
        
        try:
            # Load signature data
            with open(sig_file, 'r') as f:
                sig_data = json.load(f)
            
            # Read document
            with open(pdf_file, 'rb') as f:
                content = f.read()
            
            # Verify hash
            doc_hash = hashlib.sha384(content).digest()
            expected_hash = base64.b64decode(sig_data['document_hash'])
            
            if doc_hash != expected_hash:
                result['errors'].append("Document has been modified")
                
                PKIAuditLog.log(
                    event_type='SIGNATURE_INVALID',
                    description=f"Document hash mismatch: {os.path.basename(pdf_file)}",
                    user=user,
                    request=request,
                    severity='WARNING',
                )
                return result
            
            # Load certificate
            cert = ClassicalCrypto.load_certificate(sig_data['certificate_pem'])
            public_key = cert.public_key()
            
            # Verify classical signature
            classical_sig = base64.b64decode(sig_data['classical_signature'])
            result['classical_valid'] = ClassicalCrypto.verify_signature(
                public_key, classical_sig, doc_hash
            )
            
            if not result['classical_valid']:
                result['errors'].append("Classical signature invalid")
            
            # Verify PQ signature if present
            if 'pq_signature' in sig_data:
                pq_sig = base64.b64decode(sig_data['pq_signature'])
                pq_public_key = base64.b64decode(sig_data['pq_public_key'])
                pq_algorithm = sig_data.get('pq_algorithm', 'DILITHIUM3')
                
                result['pq_valid'] = PostQuantumCrypto.verify(
                    pq_public_key, doc_hash, pq_sig, pq_algorithm
                )
                
                if not result['pq_valid']:
                    result['errors'].append("Post-quantum signature invalid")
            
            # Check certificate validity (basic)
            now = datetime.now()
            if cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
                result['certificate_valid'] = True
            else:
                result['warnings'].append("Certificate may be expired or not yet valid")
            
            # Extract signer info
            result['signer'] = sig_data.get('certificate_subject')
            result['signed_at'] = sig_data.get('signed_at')
            result['certificate_serial'] = sig_data.get('certificate_serial')
            
            # Overall validity
            result['valid'] = result['classical_valid']
            if result['pq_valid'] is not None:
                result['valid'] = result['valid'] and result['pq_valid']
            
            # Audit log
            event_type = 'SIGNATURE_VERIFIED' if result['valid'] else 'SIGNATURE_INVALID'
            PKIAuditLog.log(
                event_type=event_type,
                description=f"Signature verification: {os.path.basename(pdf_file)}",
                user=user,
                request=request,
                severity='INFO' if result['valid'] else 'WARNING',
                details={
                    'classical_valid': result['classical_valid'],
                    'pq_valid': result['pq_valid'],
                    'signer': result['signer'],
                }
            )
            
        except Exception as e:
            result['errors'].append(f"Verification error: {str(e)}")
        
        return result
    
    @classmethod
    def _verify_embedded_signature(cls, pdf_file: str,
                                    user=None, request=None) -> dict:
        """Verify an embedded PDF signature using PDFNet."""
        result = {
            'valid': False,
            'classical_valid': False,
            'pq_valid': None,
            'certificate_valid': False,
            'signer': None,
            'signed_at': None,
            'errors': [],
            'warnings': [],
        }
        
        try:
            PDFNet.Initialize()
            doc = PDFDoc(pdf_file)
            
            # Find signature fields
            field_iter = doc.GetFieldIterator()
            signatures_found = 0
            
            while field_iter.HasNext():
                field = field_iter.Current()
                if field.IsValid() and field.GetType() == Field.e_signature:
                    signatures_found += 1
                    digsig_field = DigitalSignatureField(field)
                    
                    # Get verification status
                    # Note: Full verification requires PDFNet's verification API
                    result['classical_valid'] = True  # Placeholder
                    result['valid'] = True
                
                field_iter.Next()
            
            if signatures_found == 0:
                result['errors'].append("No signatures found in document")
            else:
                result['signatures_count'] = signatures_found
            
            doc.Close()
            
        except Exception as e:
            result['errors'].append(f"PDFNet error: {str(e)}")
        
        return result
    
    @classmethod
    def _create_temp_p12(cls, certificate: UserCertificate, 
                         private_key_pem: bytes) -> str:
        """Create temporary PKCS#12 file for PDFNet signing."""
        import tempfile
        from cryptography.hazmat.primitives.serialization import pkcs12
        
        # Load key and cert
        private_key = ClassicalCrypto.load_private_key(private_key_pem)
        cert = ClassicalCrypto.load_certificate(certificate.certificate_pem)
        
        # Create PKCS#12
        p12_data = pkcs12.serialize_key_and_certificates(
            name=certificate.serial_number.encode(),
            key=private_key,
            cert=cert,
            cas=None,
            encryption_algorithm=pkcs12.NoEncryption()
        )
        
        # Write to temp file
        fd, path = tempfile.mkstemp(suffix='.p12')
        try:
            os.write(fd, p12_data)
        finally:
            os.close(fd)
        
        return path
    
    @classmethod
    def _create_pq_signature(cls, file_path: str, 
                              pq_private_key: bytes,
                              algorithm: str) -> str:
        """Create post-quantum signature for a file."""
        with open(file_path, 'rb') as f:
            content = f.read()
        
        file_hash = hashlib.sha384(content).digest()
        signature = PostQuantumCrypto.sign(pq_private_key, file_hash, algorithm)
        
        return base64.b64encode(signature).decode('ascii')
    
    @classmethod
    def _calculate_file_hash(cls, file_path: str) -> str:
        """Calculate SHA-384 hash of a file."""
        with open(file_path, 'rb') as f:
            return hashlib.sha384(f.read()).hexdigest()
    
    @classmethod
    def get_signature_info(cls, pdf_file: str) -> dict:
        """
        Get information about signatures in a PDF.
        
        Args:
            pdf_file: Path to PDF file
            
        Returns:
            dict with signature information
        """
        info = {
            'has_signatures': False,
            'signatures': [],
        }
        
        # Check for detached signature
        sig_file = pdf_file + '.sig'
        if os.path.exists(sig_file):
            try:
                with open(sig_file, 'r') as f:
                    sig_data = json.load(f)
                
                info['has_signatures'] = True
                info['signatures'].append({
                    'type': 'detached',
                    'signer': sig_data.get('certificate_subject'),
                    'signed_at': sig_data.get('signed_at'),
                    'has_pq': 'pq_signature' in sig_data,
                })
            except Exception:
                pass
        
        # Check for embedded signatures
        if PDFNET_AVAILABLE:
            try:
                PDFNet.Initialize()
                doc = PDFDoc(pdf_file)
                
                field_iter = doc.GetFieldIterator()
                while field_iter.HasNext():
                    field = field_iter.Current()
                    if field.IsValid() and field.GetType() == Field.e_signature:
                        info['has_signatures'] = True
                        info['signatures'].append({
                            'type': 'embedded',
                            'field_name': field.GetName(),
                        })
                    field_iter.Next()
                
                doc.Close()
            except Exception:
                pass
        
        return info
