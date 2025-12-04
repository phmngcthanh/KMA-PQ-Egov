"""
Certificate Authority Service

Provides operations for:
- Creating Root and Intermediate CAs
- Managing CA lifecycle
- Generating CRLs
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from django.utils import timezone
from django.conf import settings

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes

from ..models import CertificateAuthority, CertificateRevocationList, RevokedCertificate, PKIAuditLog
from ..crypto import ClassicalCrypto, PostQuantumCrypto, HybridCrypto, CryptoUtils


class CAService:
    """
    Service for Certificate Authority operations.
    """
    
    # Default validity periods
    ROOT_CA_VALIDITY_YEARS = 20
    INTERMEDIATE_CA_VALIDITY_YEARS = 10
    
    @classmethod
    def get_master_key(cls) -> bytes:
        """
        Get the master key for encrypting CA private keys.
        
        In production, this should come from an HSM or secure key vault.
        """
        key = CryptoUtils.get_env_master_key()
        if not key:
            # For development: generate and store in file
            key_path = os.path.join(settings.BASE_DIR, '.pki_master_key')
            if os.path.exists(key_path):
                key = CryptoUtils.load_master_key(key_path)
            else:
                key = CryptoUtils.generate_and_save_master_key(key_path)
        return key
    
    @classmethod
    def create_root_ca(cls,
                       name: str,
                       common_name: str,
                       organization: str = "E-Government PKI",
                       country: str = "VN",
                       organizational_unit: str = "",
                       locality: str = "",
                       state: str = "",
                       email: str = "",
                       key_algorithm: str = "RSA_4096",
                       pq_algorithm: str = "DILITHIUM3",
                       validity_years: int = None,
                       user=None,
                       request=None) -> CertificateAuthority:
        """
        Create a new Root CA.
        
        Args:
            name: Friendly name for the CA
            common_name: Certificate CN
            organization: Organization name
            country: Country code
            organizational_unit: OU name
            locality: City/locality
            state: State/province
            email: Contact email
            key_algorithm: Classical key algorithm
            pq_algorithm: Post-quantum algorithm
            validity_years: Override default validity
            user: User creating the CA (for audit)
            request: HTTP request (for audit)
            
        Returns:
            CertificateAuthority instance
        """
        validity_years = validity_years or cls.ROOT_CA_VALIDITY_YEARS
        
        # Generate classical key pair
        private_key, public_key = ClassicalCrypto.generate_keypair(key_algorithm)
        
        # Generate post-quantum key pair
        pq_public_key, pq_private_key = PostQuantumCrypto.generate_signature_keypair(
            pq_algorithm
        )
        
        # Build subject name
        subject = ClassicalCrypto.build_subject_name(
            common_name=common_name,
            organization=organization,
            organizational_unit=organizational_unit,
            locality=locality,
            state=state,
            country=country,
            email=email
        )
        
        # Create self-signed CA certificate
        now = datetime.utcnow()
        validity_days = validity_years * 365
        
        cert = ClassicalCrypto.create_ca_certificate(
            private_key=private_key,
            public_key=public_key,
            subject_name=subject,
            is_root=True,
            validity_days=validity_days,
            path_length=2  # Allow 2 levels of subordinate CAs
        )
        
        # Serialize keys
        private_key_pem = ClassicalCrypto.serialize_private_key(private_key)
        public_key_pem = ClassicalCrypto.serialize_public_key(public_key)
        cert_pem = ClassicalCrypto.serialize_certificate(cert)
        
        # Encrypt private keys
        master_key = cls.get_master_key()
        encrypted_private_key = ClassicalCrypto.encrypt_private_key(
            private_key_pem, master_key
        )
        encrypted_pq_private_key = ClassicalCrypto.encrypt_private_key(
            pq_private_key, master_key
        )
        
        # Generate serial number
        serial_number = format(cert.serial_number, 'X')
        
        # Create CA record
        ca = CertificateAuthority.objects.create(
            name=name,
            common_name=common_name,
            organization=organization,
            organizational_unit=organizational_unit,
            locality=locality,
            state=state,
            country=country,
            email=email,
            ca_type='ROOT',
            parent_ca=None,
            path_length=2,
            key_algorithm=key_algorithm,
            certificate_pem=cert_pem.decode('utf-8'),
            private_key_pem_encrypted=encrypted_private_key,
            public_key_pem=public_key_pem.decode('utf-8'),
            pq_algorithm=pq_algorithm,
            pq_public_key=pq_public_key,
            pq_private_key_encrypted=encrypted_pq_private_key,
            serial_number=serial_number,
            valid_from=timezone.make_aware(now),
            valid_until=timezone.make_aware(now + timedelta(days=validity_days)),
            key_usage=['keyCertSign', 'cRLSign', 'digitalSignature'],
            is_active=True,
        )
        
        # Audit log
        PKIAuditLog.log(
            event_type='CA_CREATED',
            description=f"Root CA created: {name}",
            user=user,
            request=request,
            ca=ca,
            severity='INFO',
            details={
                'ca_type': 'ROOT',
                'key_algorithm': key_algorithm,
                'pq_algorithm': pq_algorithm,
                'validity_years': validity_years,
            }
        )
        
        return ca
    
    @classmethod
    def create_intermediate_ca(cls,
                               name: str,
                               common_name: str,
                               parent_ca: CertificateAuthority,
                               ca_type: str,
                               organization: str = None,
                               country: str = None,
                               organizational_unit: str = "",
                               key_algorithm: str = None,
                               pq_algorithm: str = None,
                               validity_years: int = None,
                               user=None,
                               request=None) -> CertificateAuthority:
        """
        Create an Intermediate CA signed by a parent CA.
        
        Args:
            name: Friendly name
            common_name: Certificate CN
            parent_ca: Parent CA to sign this intermediate
            ca_type: Type (INTERMEDIATE_OFFICER, INTERMEDIATE_CITIZEN, INTERMEDIATE_SERVICE)
            organization: Override parent organization
            country: Override parent country
            organizational_unit: OU name
            key_algorithm: Override parent key algorithm
            pq_algorithm: Override parent PQ algorithm
            validity_years: Override default validity
            user: User creating the CA
            request: HTTP request
            
        Returns:
            CertificateAuthority instance
        """
        if not parent_ca.is_valid():
            raise ValueError("Parent CA is not valid")
        
        if parent_ca.path_length is not None and parent_ca.path_length <= 0:
            raise ValueError("Parent CA cannot issue subordinate CAs")
        
        # Inherit settings from parent if not specified
        organization = organization or parent_ca.organization
        country = country or parent_ca.country
        key_algorithm = key_algorithm or parent_ca.key_algorithm
        pq_algorithm = pq_algorithm or parent_ca.pq_algorithm
        validity_years = validity_years or cls.INTERMEDIATE_CA_VALIDITY_YEARS
        
        # Generate key pairs
        private_key, public_key = ClassicalCrypto.generate_keypair(key_algorithm)
        pq_public_key, pq_private_key = PostQuantumCrypto.generate_signature_keypair(
            pq_algorithm
        )
        
        # Build subject
        subject = ClassicalCrypto.build_subject_name(
            common_name=common_name,
            organization=organization,
            organizational_unit=organizational_unit,
            country=country
        )
        
        # Decrypt parent's private key
        master_key = cls.get_master_key()
        parent_private_key_pem = ClassicalCrypto.decrypt_private_key(
            parent_ca.private_key_pem_encrypted, master_key
        )
        parent_private_key = ClassicalCrypto.load_private_key(parent_private_key_pem)
        parent_cert = ClassicalCrypto.load_certificate(parent_ca.certificate_pem)
        
        # Create intermediate CA certificate
        now = datetime.utcnow()
        validity_days = validity_years * 365
        
        # Calculate path length (one less than parent)
        path_length = None
        if parent_ca.path_length is not None:
            path_length = max(0, parent_ca.path_length - 1)
        
        cert = ClassicalCrypto.create_ca_certificate(
            private_key=private_key,
            public_key=public_key,
            subject_name=subject,
            is_root=False,
            parent_cert=parent_cert,
            parent_key=parent_private_key,
            validity_days=validity_days,
            path_length=path_length
        )
        
        # Serialize and encrypt
        private_key_pem = ClassicalCrypto.serialize_private_key(private_key)
        public_key_pem = ClassicalCrypto.serialize_public_key(public_key)
        cert_pem = ClassicalCrypto.serialize_certificate(cert)
        
        encrypted_private_key = ClassicalCrypto.encrypt_private_key(
            private_key_pem, master_key
        )
        encrypted_pq_private_key = ClassicalCrypto.encrypt_private_key(
            pq_private_key, master_key
        )
        
        serial_number = format(cert.serial_number, 'X')
        
        # Create CA record
        ca = CertificateAuthority.objects.create(
            name=name,
            common_name=common_name,
            organization=organization,
            organizational_unit=organizational_unit,
            country=country,
            ca_type=ca_type,
            parent_ca=parent_ca,
            path_length=path_length,
            key_algorithm=key_algorithm,
            certificate_pem=cert_pem.decode('utf-8'),
            private_key_pem_encrypted=encrypted_private_key,
            public_key_pem=public_key_pem.decode('utf-8'),
            pq_algorithm=pq_algorithm,
            pq_public_key=pq_public_key,
            pq_private_key_encrypted=encrypted_pq_private_key,
            serial_number=serial_number,
            valid_from=timezone.make_aware(now),
            valid_until=timezone.make_aware(now + timedelta(days=validity_days)),
            key_usage=['keyCertSign', 'cRLSign', 'digitalSignature'],
            is_active=True,
        )
        
        # Audit log
        PKIAuditLog.log(
            event_type='CA_CREATED',
            description=f"Intermediate CA created: {name}",
            user=user,
            request=request,
            ca=ca,
            severity='INFO',
            details={
                'ca_type': ca_type,
                'parent_ca': str(parent_ca.id),
                'key_algorithm': key_algorithm,
                'pq_algorithm': pq_algorithm,
                'validity_years': validity_years,
            }
        )
        
        return ca
    
    @classmethod
    def get_ca_for_cert_type(cls, cert_type: str) -> Optional[CertificateAuthority]:
        """
        Get the appropriate CA for issuing a certificate type.
        
        Args:
            cert_type: OFFICER, CITIZEN, or SERVICE
            
        Returns:
            CertificateAuthority or None
        """
        ca_type_mapping = {
            'OFFICER': 'INTERMEDIATE_OFFICER',
            'CITIZEN': 'INTERMEDIATE_CITIZEN',
            'SERVICE': 'INTERMEDIATE_SERVICE',
        }
        
        ca_type = ca_type_mapping.get(cert_type)
        if not ca_type:
            return None
        
        return CertificateAuthority.objects.filter(
            ca_type=ca_type,
            is_active=True,
            is_compromised=False,
            valid_until__gt=timezone.now()
        ).first()
    
    @classmethod
    def generate_crl(cls, ca: CertificateAuthority,
                     user=None, request=None) -> CertificateRevocationList:
        """
        Generate a new CRL for a CA.
        
        Args:
            ca: Certificate Authority
            user: User generating CRL
            request: HTTP request
            
        Returns:
            CertificateRevocationList instance
        """
        from ..models import UserCertificate
        
        # Get all revoked certificates for this CA
        revoked_certs = UserCertificate.objects.filter(
            issuing_ca=ca,
            status='REVOKED'
        ).select_related('revocation_entry')
        
        # Build CRL entries
        builder = x509.CertificateRevocationListBuilder()
        
        # Load CA certificate and key
        ca_cert = ClassicalCrypto.load_certificate(ca.certificate_pem)
        master_key = cls.get_master_key()
        ca_private_key_pem = ClassicalCrypto.decrypt_private_key(
            ca.private_key_pem_encrypted, master_key
        )
        ca_private_key = ClassicalCrypto.load_private_key(ca_private_key_pem)
        
        builder = builder.issuer_name(ca_cert.subject)
        
        now = datetime.utcnow()
        next_update = now + timedelta(days=ca.crl_validity_days)
        
        builder = builder.last_update(now)
        builder = builder.next_update(next_update)
        
        # Increment CRL number
        crl_number = ca.last_crl_number + 1
        
        # Add revoked certificates
        for cert in revoked_certs:
            try:
                revocation_entry = cert.revocation_entry
                revoked_cert = x509.RevokedCertificateBuilder().serial_number(
                    int(cert.serial_number, 16)
                ).revocation_date(
                    revocation_entry.revocation_date.replace(tzinfo=None)
                ).build()
                builder = builder.add_revoked_certificate(revoked_cert)
            except RevokedCertificate.DoesNotExist:
                pass
        
        # Sign CRL
        crl = builder.sign(ca_private_key, hashes.SHA384())
        
        # Serialize
        crl_pem = crl.public_bytes(encoding=x509.serialization.Encoding.PEM)
        crl_der = crl.public_bytes(encoding=x509.serialization.Encoding.DER)
        
        # Save CRL
        crl_record = CertificateRevocationList.objects.create(
            issuing_ca=ca,
            crl_number=crl_number,
            this_update=timezone.make_aware(now),
            next_update=timezone.make_aware(next_update),
            crl_pem=crl_pem.decode('utf-8'),
            crl_der=crl_der,
            signature_algorithm='SHA384WithRSA',
            entries_count=revoked_certs.count(),
        )
        
        # Update CA
        ca.last_crl_number = crl_number
        ca.next_crl_update = timezone.make_aware(next_update)
        ca.save(update_fields=['last_crl_number', 'next_crl_update'])
        
        # Audit log
        PKIAuditLog.log(
            event_type='CRL_GENERATED',
            description=f"CRL #{crl_number} generated for {ca.name}",
            user=user,
            request=request,
            ca=ca,
            severity='INFO',
            details={
                'crl_number': crl_number,
                'entries_count': revoked_certs.count(),
                'next_update': next_update.isoformat(),
            }
        )
        
        return crl_record
    
    @classmethod
    def get_decrypted_private_key(cls, ca: CertificateAuthority):
        """
        Get decrypted private key for a CA.
        
        Args:
            ca: Certificate Authority
            
        Returns:
            Private key object
        """
        master_key = cls.get_master_key()
        private_key_pem = ClassicalCrypto.decrypt_private_key(
            ca.private_key_pem_encrypted, master_key
        )
        return ClassicalCrypto.load_private_key(private_key_pem)
    
    @classmethod
    def get_decrypted_pq_private_key(cls, ca: CertificateAuthority) -> bytes:
        """
        Get decrypted post-quantum private key for a CA.
        
        Args:
            ca: Certificate Authority
            
        Returns:
            Private key bytes
        """
        if not ca.pq_private_key_encrypted:
            return None
        
        master_key = cls.get_master_key()
        return ClassicalCrypto.decrypt_private_key(
            ca.pq_private_key_encrypted, master_key
        )
    
    @classmethod
    def deactivate_ca(cls, ca: CertificateAuthority,
                      reason: str, user=None, request=None):
        """
        Deactivate a CA.
        
        Args:
            ca: Certificate Authority to deactivate
            reason: Reason for deactivation
            user: User performing action
            request: HTTP request
        """
        ca.is_active = False
        ca.save(update_fields=['is_active', 'updated_at'])
        
        PKIAuditLog.log(
            event_type='CA_DEACTIVATED',
            description=f"CA deactivated: {ca.name}",
            user=user,
            request=request,
            ca=ca,
            severity='WARNING',
            details={'reason': reason}
        )
    
    @classmethod
    def mark_ca_compromised(cls, ca: CertificateAuthority,
                            reason: str, user=None, request=None):
        """
        Mark a CA as compromised.
        
        This is a critical security event. All certificates issued
        by this CA should be considered invalid.
        
        Args:
            ca: Certificate Authority
            reason: Description of compromise
            user: User reporting compromise
            request: HTTP request
        """
        ca.is_compromised = True
        ca.is_active = False
        ca.save(update_fields=['is_compromised', 'is_active', 'updated_at'])
        
        PKIAuditLog.log(
            event_type='CA_DEACTIVATED',
            description=f"CA COMPROMISED: {ca.name}",
            user=user,
            request=request,
            ca=ca,
            severity='CRITICAL',
            details={'reason': reason, 'compromised': True}
        )
