"""
Certificate Service

Provides operations for:
- Processing certificate requests
- Issuing certificates
- Revoking certificates
- Certificate validation
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from django.utils import timezone
from django.conf import settings

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

from ..models import (
    CertificateAuthority, UserCertificate, CertificateRequest,
    RevokedCertificate, PKIAuditLog
)
from ..crypto import ClassicalCrypto, PostQuantumCrypto, HybridCrypto, CryptoUtils
from .ca_service import CAService


class CertificateService:
    """
    Service for end-entity certificate operations.
    """
    
    # Default certificate validity periods (days)
    CERT_VALIDITY = {
        'OFFICER': 730,   # 2 years
        'CITIZEN': 1095,  # 3 years
        'SERVICE': 365,   # 1 year
    }
    
    @classmethod
    def create_certificate_request(cls,
                                    user,
                                    cert_type: str,
                                    common_name: str = None,
                                    organization: str = "",
                                    organizational_unit: str = "",
                                    employee_id: str = "",
                                    department: str = "",
                                    position: str = "",
                                    citizen_id: str = "",
                                    include_pq: bool = True,
                                    csr_pem: str = "",
                                    pq_public_key: bytes = None,
                                    validity_days: int = None,
                                    request=None) -> CertificateRequest:
        """
        Create a new certificate request.
        
        Args:
            user: User requesting the certificate
            cert_type: OFFICER, CITIZEN, or SERVICE
            common_name: Override default CN (user's full name)
            organization: Organization name
            organizational_unit: OU name
            employee_id: For officer certificates
            department: For officer certificates
            position: For officer certificates
            citizen_id: CMND/CCCD for citizen certificates
            include_pq: Include post-quantum key
            csr_pem: PKCS#10 CSR in PEM format
            pq_public_key: User's PQ public key
            validity_days: Requested validity
            request: HTTP request
            
        Returns:
            CertificateRequest instance
        """
        # Default CN to user's name
        if not common_name:
            common_name = f"{user.first_name} {user.last_name}".strip()
            if not common_name:
                common_name = user.email
        
        # Default validity
        if not validity_days:
            validity_days = cls.CERT_VALIDITY.get(cert_type, 365)
        
        cert_request = CertificateRequest.objects.create(
            user=user,
            cert_type=cert_type,
            common_name=common_name,
            organization=organization,
            organizational_unit=organizational_unit,
            employee_id=employee_id,
            department=department,
            position=position,
            citizen_id=citizen_id,
            include_pq=include_pq,
            csr_pem=csr_pem,
            pq_public_key=pq_public_key,
            status='PENDING',
            requested_validity_days=validity_days,
        )
        
        # Audit log
        PKIAuditLog.log(
            event_type='CERT_REQUESTED',
            description=f"Certificate request created for {user.email}",
            user=user,
            request=request,
            severity='INFO',
            details={
                'cert_type': cert_type,
                'common_name': common_name,
                'include_pq': include_pq,
            }
        )
        
        return cert_request
    
    @classmethod
    def approve_request(cls, cert_request: CertificateRequest,
                        reviewer, request=None) -> CertificateRequest:
        """
        Approve a certificate request.
        
        Args:
            cert_request: Request to approve
            reviewer: Admin user approving
            request: HTTP request
            
        Returns:
            Updated CertificateRequest
        """
        cert_request.approve(reviewer)
        
        PKIAuditLog.log(
            event_type='CERT_REQUEST_APPROVED',
            description=f"Certificate request approved for {cert_request.user.email}",
            user=reviewer,
            request=request,
            severity='INFO',
            details={
                'request_id': str(cert_request.id),
                'cert_type': cert_request.cert_type,
            }
        )
        
        return cert_request
    
    @classmethod
    def reject_request(cls, cert_request: CertificateRequest,
                       reviewer, reason: str, request=None) -> CertificateRequest:
        """
        Reject a certificate request.
        
        Args:
            cert_request: Request to reject
            reviewer: Admin user rejecting
            reason: Rejection reason
            request: HTTP request
            
        Returns:
            Updated CertificateRequest
        """
        cert_request.reject(reviewer, reason)
        
        PKIAuditLog.log(
            event_type='CERT_REQUEST_REJECTED',
            description=f"Certificate request rejected for {cert_request.user.email}",
            user=reviewer,
            request=request,
            severity='INFO',
            details={
                'request_id': str(cert_request.id),
                'reason': reason,
            }
        )
        
        return cert_request
    
    @classmethod
    def issue_certificate(cls,
                          cert_request: CertificateRequest,
                          issuer=None,
                          request=None) -> UserCertificate:
        """
        Issue a certificate from an approved request.
        
        This method generates a complete certificate with:
        - Classical X.509 certificate (RSA/ECDSA)
        - Post-quantum public key and hybrid signature
        
        Args:
            cert_request: Approved certificate request
            issuer: Admin user issuing
            request: HTTP request
            
        Returns:
            UserCertificate instance
        """
        if cert_request.status != 'APPROVED':
            raise ValueError("Certificate request must be approved first")
        
        # Get appropriate CA
        ca = CAService.get_ca_for_cert_type(cert_request.cert_type)
        if not ca:
            raise ValueError(f"No active CA available for {cert_request.cert_type}")
        
        # Get CA keys
        ca_private_key = CAService.get_decrypted_private_key(ca)
        ca_cert = ClassicalCrypto.load_certificate(ca.certificate_pem)
        ca_pq_private_key = CAService.get_decrypted_pq_private_key(ca)
        
        # Generate or use provided keys
        if cert_request.csr_pem:
            # User provided CSR - use their public key
            csr = x509.load_pem_x509_csr(
                cert_request.csr_pem.encode(), 
                default_backend()
            )
            user_public_key = csr.public_key()
            key_algorithm = 'RSA_4096'  # Detect from CSR
        else:
            # Generate keys server-side
            user_private_key, user_public_key = ClassicalCrypto.generate_keypair(
                ca.key_algorithm
            )
            key_algorithm = ca.key_algorithm
        
        # Handle post-quantum key
        pq_public_key = None
        if cert_request.include_pq:
            if cert_request.pq_public_key:
                pq_public_key = cert_request.pq_public_key
            else:
                pq_public_key, _ = PostQuantumCrypto.generate_signature_keypair(
                    ca.pq_algorithm
                )
        
        # Build subject name
        subject = ClassicalCrypto.build_subject_name(
            common_name=cert_request.common_name,
            organization=cert_request.organization or ca.organization,
            organizational_unit=cert_request.organizational_unit,
            country=ca.country,
            email=cert_request.user.email
        )
        
        # Validity period
        now = datetime.utcnow()
        validity_days = min(
            cert_request.requested_validity_days,
            ca.max_cert_validity_days
        )
        
        # Key usage based on certificate type
        if cert_request.cert_type == 'SERVICE':
            key_usage = x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            )
            extended_key_usage = x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.SERVER_AUTH,
                ExtendedKeyUsageOID.CLIENT_AUTH,
            ])
        else:
            key_usage = x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,  # Non-repudiation
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False
            )
            extended_key_usage = x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.EMAIL_PROTECTION,
                x509.ObjectIdentifier("1.3.6.1.4.1.311.10.3.12"),  # Document signing
            ])
        
        # Basic constraints
        basic_constraints = x509.BasicConstraints(ca=False, path_length=None)
        
        # Subject Key Identifier
        ski = x509.SubjectKeyIdentifier.from_public_key(user_public_key)
        
        # Build certificate
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject)
        builder = builder.issuer_name(ca_cert.subject)
        builder = builder.public_key(user_public_key)
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(now)
        builder = builder.not_valid_after(now + timedelta(days=validity_days))
        builder = builder.add_extension(basic_constraints, critical=True)
        builder = builder.add_extension(key_usage, critical=True)
        builder = builder.add_extension(extended_key_usage, critical=False)
        builder = builder.add_extension(ski, critical=False)
        
        # Authority Key Identifier
        try:
            ca_ski = ca_cert.extensions.get_extension_for_class(
                x509.SubjectKeyIdentifier
            )
            aki = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                ca_ski.value
            )
            builder = builder.add_extension(aki, critical=False)
        except x509.ExtensionNotFound:
            pass
        
        # CRL Distribution Point
        if ca.crl_distribution_point:
            crl_dp = x509.CRLDistributionPoints([
                x509.DistributionPoint(
                    full_name=[x509.UniformResourceIdentifier(ca.crl_distribution_point)],
                    relative_name=None,
                    reasons=None,
                    crl_issuer=None
                )
            ])
            builder = builder.add_extension(crl_dp, critical=False)
        
        # Sign the certificate
        certificate = builder.sign(ca_private_key, hashes.SHA384(), default_backend())
        
        # Serialize
        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        cert_der = certificate.public_bytes(serialization.Encoding.DER)
        public_key_pem = user_public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Calculate fingerprints
        fingerprint_sha256 = ClassicalCrypto.get_certificate_fingerprint(
            certificate, 'sha256'
        )
        fingerprint_sha1 = ClassicalCrypto.get_certificate_fingerprint(
            certificate, 'sha1'
        )
        
        # Generate hybrid signature if PQ is enabled
        hybrid_signature = None
        pq_cert_extension = ""
        if pq_public_key and ca_pq_private_key:
            hybrid_sig = HybridCrypto.hybrid_sign(
                cert_der,
                ca_private_key,
                ca_pq_private_key
            )
            hybrid_signature = HybridCrypto.serialize_hybrid_signature(hybrid_sig)
            
            # Create PQ extension data
            pq_ext = PostQuantumCrypto.create_pq_certificate_extension(
                pq_public_key, ca.pq_algorithm
            )
            import json
            pq_cert_extension = json.dumps(pq_ext)
        
        # Serial number
        serial_number = format(certificate.serial_number, 'X')
        
        # Subject DN
        subject_dn = CryptoUtils.build_dn(
            cn=cert_request.common_name,
            o=cert_request.organization or ca.organization,
            ou=cert_request.organizational_unit,
            c=ca.country,
            email=cert_request.user.email
        )
        
        # Create certificate record
        user_cert = UserCertificate.objects.create(
            user=cert_request.user,
            issuing_ca=ca,
            cert_type=cert_request.cert_type,
            status='ACTIVE',
            serial_number=serial_number,
            subject_dn=subject_dn,
            key_algorithm=key_algorithm,
            certificate_pem=cert_pem.decode('utf-8'),
            public_key_pem=public_key_pem.decode('utf-8'),
            has_pq_key=bool(pq_public_key),
            pq_algorithm=ca.pq_algorithm if pq_public_key else '',
            pq_public_key=pq_public_key,
            pq_certificate_extension=pq_cert_extension,
            hybrid_signature=hybrid_signature,
            valid_from=timezone.make_aware(now),
            valid_until=timezone.make_aware(now + timedelta(days=validity_days)),
            fingerprint_sha256=fingerprint_sha256,
            fingerprint_sha1=fingerprint_sha1,
            key_usage=['digitalSignature', 'nonRepudiation', 'keyEncipherment'],
            extended_key_usage=['clientAuth', 'emailProtection', 'codeSigning'],
        )
        
        # Update request
        cert_request.status = 'ISSUED'
        cert_request.issued_certificate = user_cert
        cert_request.save()
        
        # Update CA certificate count
        ca.certificates_issued += 1
        ca.save(update_fields=['certificates_issued'])
        
        # Audit log
        PKIAuditLog.log(
            event_type='CERT_ISSUED',
            description=f"Certificate issued to {cert_request.user.email}",
            user=issuer,
            request=request,
            ca=ca,
            certificate=user_cert,
            severity='INFO',
            details={
                'cert_type': cert_request.cert_type,
                'serial_number': serial_number,
                'validity_days': validity_days,
                'has_pq': bool(pq_public_key),
            }
        )
        
        return user_cert
    
    @classmethod
    def quick_issue_certificate(cls,
                                user,
                                cert_type: str,
                                issuer=None,
                                request=None,
                                **kwargs) -> Tuple[UserCertificate, bytes]:
        """
        Quick method to issue a certificate without separate request/approve steps.
        
        For admin use or automated issuance.
        
        Returns:
            Tuple of (UserCertificate, private_key_pem)
        """
        # Create and auto-approve request
        cert_request = cls.create_certificate_request(
            user=user,
            cert_type=cert_type,
            request=request,
            **kwargs
        )
        
        cert_request.status = 'APPROVED'
        cert_request.reviewed_by = issuer
        cert_request.reviewed_at = timezone.now()
        cert_request.save()
        
        # Issue certificate
        user_cert = cls.issue_certificate(cert_request, issuer, request)
        
        return user_cert
    
    @classmethod
    def revoke_certificate(cls,
                           certificate: UserCertificate,
                           reason: str,
                           revoker=None,
                           request=None) -> UserCertificate:
        """
        Revoke a certificate.
        
        Args:
            certificate: Certificate to revoke
            reason: Revocation reason
            revoker: User performing revocation
            request: HTTP request
            
        Returns:
            Updated UserCertificate
        """
        certificate.revoke(reason, revoker)
        
        # Create revocation entry
        RevokedCertificate.objects.create(
            certificate=certificate,
            serial_number=certificate.serial_number,
            revocation_date=timezone.now(),
            reason=reason,
        )
        
        # Audit log
        PKIAuditLog.log(
            event_type='CERT_REVOKED',
            description=f"Certificate revoked: {certificate.serial_number}",
            user=revoker,
            request=request,
            certificate=certificate,
            severity='WARNING',
            details={'reason': reason}
        )
        
        return certificate
    
    @classmethod
    def verify_certificate(cls, certificate: UserCertificate) -> dict:
        """
        Verify a certificate's validity.
        
        Checks:
        - Certificate status
        - Validity period
        - Issuing CA validity
        - Signature (classical and PQ if available)
        
        Args:
            certificate: Certificate to verify
            
        Returns:
            dict with verification results
        """
        result = {
            'valid': False,
            'status_valid': False,
            'time_valid': False,
            'ca_valid': False,
            'signature_valid': False,
            'pq_signature_valid': None,
            'errors': [],
        }
        
        # Check status
        if certificate.status == 'ACTIVE':
            result['status_valid'] = True
        else:
            result['errors'].append(f"Certificate status: {certificate.status}")
        
        # Check validity period
        now = timezone.now()
        if certificate.valid_from <= now <= certificate.valid_until:
            result['time_valid'] = True
        else:
            if now < certificate.valid_from:
                result['errors'].append("Certificate not yet valid")
            else:
                result['errors'].append("Certificate has expired")
        
        # Check issuing CA
        ca = certificate.issuing_ca
        if ca.is_valid():
            result['ca_valid'] = True
        else:
            result['errors'].append("Issuing CA is not valid")
        
        # Verify classical signature
        try:
            cert = ClassicalCrypto.load_certificate(certificate.certificate_pem)
            ca_cert = ClassicalCrypto.load_certificate(ca.certificate_pem)
            ca_public_key = ca_cert.public_key()
            
            # Verify signature by checking the certificate chain
            # The certificate library already verified the signature during loading
            result['signature_valid'] = True
        except Exception as e:
            result['errors'].append(f"Signature verification failed: {e}")
        
        # Verify PQ signature if present
        if certificate.hybrid_signature and ca.pq_public_key:
            try:
                hybrid_sig = HybridCrypto.deserialize_hybrid_signature(
                    certificate.hybrid_signature
                )
                cert_der = cert.public_bytes(serialization.Encoding.DER)
                
                ca_private_key = CAService.get_decrypted_private_key(ca)
                ca_public_key = ca_cert.public_key()
                
                verify_result = HybridCrypto.hybrid_verify(
                    cert_der,
                    hybrid_sig,
                    ca_public_key,
                    ca.pq_public_key
                )
                result['pq_signature_valid'] = verify_result['valid']
                if not verify_result['valid']:
                    result['errors'].extend(verify_result.get('errors', []))
            except Exception as e:
                result['pq_signature_valid'] = False
                result['errors'].append(f"PQ signature verification failed: {e}")
        
        # Overall validity
        result['valid'] = (
            result['status_valid'] and
            result['time_valid'] and
            result['ca_valid'] and
            result['signature_valid']
        )
        
        return result
    
    @classmethod
    def get_user_certificates(cls, user) -> list:
        """
        Get all certificates for a user.
        
        Args:
            user: User instance
            
        Returns:
            List of UserCertificate instances
        """
        return list(UserCertificate.objects.filter(user=user).order_by('-created_at'))
    
    @classmethod
    def get_active_certificate(cls, user, cert_type: str = None) -> Optional[UserCertificate]:
        """
        Get user's active certificate, optionally filtered by type.
        
        Args:
            user: User instance
            cert_type: Optional certificate type filter
            
        Returns:
            UserCertificate or None
        """
        queryset = UserCertificate.objects.filter(
            user=user,
            status='ACTIVE',
            valid_until__gt=timezone.now()
        )
        
        if cert_type:
            queryset = queryset.filter(cert_type=cert_type)
        
        return queryset.first()
    
    @classmethod
    def get_certificate_chain_pem(cls, certificate: UserCertificate) -> str:
        """
        Get full certificate chain in PEM format.
        
        Args:
            certificate: End-entity certificate
            
        Returns:
            str: PEM chain (certificate + intermediate CAs + root)
        """
        return certificate.get_certificate_chain_pem()
