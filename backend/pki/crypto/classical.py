"""
Classical Cryptography Module

Provides RSA and ECDSA operations for:
- Key generation
- Certificate creation
- Digital signatures
- Signature verification
"""

from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime, timedelta
import secrets
import os


class ClassicalCrypto:
    """
    Classical cryptography operations using RSA and ECDSA.
    
    Supports:
    - RSA-2048, RSA-4096
    - ECDSA P-256, P-384
    """
    
    # Algorithm configurations
    RSA_KEY_SIZES = {
        'RSA_2048': 2048,
        'RSA_4096': 4096,
    }
    
    ECDSA_CURVES = {
        'ECDSA_P256': ec.SECP256R1(),
        'ECDSA_P384': ec.SECP384R1(),
    }
    
    @classmethod
    def generate_rsa_keypair(cls, key_size=4096):
        """
        Generate an RSA key pair.
        
        Args:
            key_size: Key size in bits (2048 or 4096)
            
        Returns:
            tuple: (private_key, public_key) objects
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    @classmethod
    def generate_ecdsa_keypair(cls, curve='ECDSA_P384'):
        """
        Generate an ECDSA key pair.
        
        Args:
            curve: Curve name ('ECDSA_P256' or 'ECDSA_P384')
            
        Returns:
            tuple: (private_key, public_key) objects
        """
        curve_obj = cls.ECDSA_CURVES.get(curve, ec.SECP384R1())
        private_key = ec.generate_private_key(curve_obj, default_backend())
        public_key = private_key.public_key()
        return private_key, public_key
    
    @classmethod
    def generate_keypair(cls, algorithm='RSA_4096'):
        """
        Generate a key pair based on algorithm specification.
        
        Args:
            algorithm: Key algorithm (RSA_2048, RSA_4096, ECDSA_P256, ECDSA_P384)
            
        Returns:
            tuple: (private_key, public_key) objects
        """
        if algorithm.startswith('RSA'):
            key_size = cls.RSA_KEY_SIZES.get(algorithm, 4096)
            return cls.generate_rsa_keypair(key_size)
        elif algorithm.startswith('ECDSA'):
            return cls.generate_ecdsa_keypair(algorithm)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    @classmethod
    def serialize_private_key(cls, private_key, password=None):
        """
        Serialize private key to PEM format.
        
        Args:
            private_key: Private key object
            password: Optional password for encryption
            
        Returns:
            bytes: PEM-encoded private key
        """
        if password:
            encryption = serialization.BestAvailableEncryption(
                password.encode() if isinstance(password, str) else password
            )
        else:
            encryption = serialization.NoEncryption()
        
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
    
    @classmethod
    def serialize_public_key(cls, public_key):
        """
        Serialize public key to PEM format.
        
        Args:
            public_key: Public key object
            
        Returns:
            bytes: PEM-encoded public key
        """
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    @classmethod
    def load_private_key(cls, pem_data, password=None):
        """
        Load private key from PEM format.
        
        Args:
            pem_data: PEM-encoded private key
            password: Optional password for decryption
            
        Returns:
            Private key object
        """
        if isinstance(pem_data, str):
            pem_data = pem_data.encode()
        if isinstance(password, str):
            password = password.encode()
        
        return serialization.load_pem_private_key(
            pem_data,
            password=password,
            backend=default_backend()
        )
    
    @classmethod
    def load_public_key(cls, pem_data):
        """
        Load public key from PEM format.
        
        Args:
            pem_data: PEM-encoded public key
            
        Returns:
            Public key object
        """
        if isinstance(pem_data, str):
            pem_data = pem_data.encode()
        
        return serialization.load_pem_public_key(
            pem_data,
            backend=default_backend()
        )
    
    @classmethod
    def encrypt_private_key(cls, private_key_pem, master_key):
        """
        Encrypt private key with AES-256-GCM.
        
        Args:
            private_key_pem: PEM-encoded private key
            master_key: 32-byte encryption key
            
        Returns:
            bytes: Encrypted private key (nonce + ciphertext + tag)
        """
        if isinstance(private_key_pem, str):
            private_key_pem = private_key_pem.encode()
        
        aesgcm = AESGCM(master_key)
        nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, private_key_pem, None)
        
        # Return nonce + ciphertext (tag is appended by AESGCM)
        return nonce + ciphertext
    
    @classmethod
    def decrypt_private_key(cls, encrypted_data, master_key):
        """
        Decrypt private key encrypted with AES-256-GCM.
        
        Args:
            encrypted_data: Encrypted data (nonce + ciphertext + tag)
            master_key: 32-byte decryption key
            
        Returns:
            bytes: Decrypted PEM-encoded private key
        """
        aesgcm = AESGCM(master_key)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    @classmethod
    def sign_data(cls, private_key, data):
        """
        Sign data using the private key.
        
        Args:
            private_key: Private key object
            data: Data to sign (bytes)
            
        Returns:
            bytes: Signature
        """
        if isinstance(data, str):
            data = data.encode()
        
        if isinstance(private_key, rsa.RSAPrivateKey):
            signature = private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA384()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA384()
            )
        elif isinstance(private_key, ec.EllipticCurvePrivateKey):
            signature = private_key.sign(
                data,
                ec.ECDSA(hashes.SHA384())
            )
        else:
            raise ValueError("Unsupported key type")
        
        return signature
    
    @classmethod
    def verify_signature(cls, public_key, signature, data):
        """
        Verify a signature.
        
        Args:
            public_key: Public key object
            signature: Signature bytes
            data: Original data (bytes)
            
        Returns:
            bool: True if signature is valid
        """
        if isinstance(data, str):
            data = data.encode()
        
        try:
            if isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    signature,
                    data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA384()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA384()
                )
            elif isinstance(public_key, ec.EllipticCurvePublicKey):
                public_key.verify(
                    signature,
                    data,
                    ec.ECDSA(hashes.SHA384())
                )
            else:
                raise ValueError("Unsupported key type")
            return True
        except Exception:
            return False
    
    @classmethod
    def create_ca_certificate(cls, private_key, public_key, subject_name,
                             is_root=True, parent_cert=None, parent_key=None,
                             validity_days=3650, path_length=None):
        """
        Create a CA certificate.
        
        Args:
            private_key: CA private key
            public_key: CA public key
            subject_name: x509.Name object for subject
            is_root: Whether this is a root CA
            parent_cert: Parent CA certificate (for intermediate)
            parent_key: Parent CA private key (for intermediate)
            validity_days: Certificate validity in days
            path_length: Path length constraint for subordinate CAs
            
        Returns:
            x509.Certificate object
        """
        now = datetime.utcnow()
        
        # Issuer is self for root, parent for intermediate
        if is_root:
            issuer_name = subject_name
            signing_key = private_key
        else:
            issuer_name = parent_cert.subject
            signing_key = parent_key
        
        # Basic constraints
        bc = x509.BasicConstraints(ca=True, path_length=path_length)
        
        # Key usage for CA
        ku = x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False
        )
        
        # Subject Key Identifier
        ski = x509.SubjectKeyIdentifier.from_public_key(public_key)
        
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(subject_name)
        builder = builder.issuer_name(issuer_name)
        builder = builder.public_key(public_key)
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(now)
        builder = builder.not_valid_after(now + timedelta(days=validity_days))
        builder = builder.add_extension(bc, critical=True)
        builder = builder.add_extension(ku, critical=True)
        builder = builder.add_extension(ski, critical=False)
        
        # Authority Key Identifier
        if not is_root and parent_cert:
            try:
                parent_ski = parent_cert.extensions.get_extension_for_class(
                    x509.SubjectKeyIdentifier
                )
                aki = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                    parent_ski.value
                )
                builder = builder.add_extension(aki, critical=False)
            except x509.ExtensionNotFound:
                pass
        
        # Sign the certificate
        if isinstance(signing_key, rsa.RSAPrivateKey):
            certificate = builder.sign(signing_key, hashes.SHA384(), default_backend())
        else:
            certificate = builder.sign(signing_key, hashes.SHA384(), default_backend())
        
        return certificate
    
    @classmethod
    def create_end_entity_certificate(cls, csr, issuer_cert, issuer_key,
                                       validity_days=365, cert_type='CITIZEN'):
        """
        Create an end-entity certificate from a CSR.
        
        Args:
            csr: x509.CertificateSigningRequest
            issuer_cert: Issuing CA certificate
            issuer_key: Issuing CA private key
            validity_days: Certificate validity
            cert_type: Type of certificate (OFFICER, CITIZEN, SERVICE)
            
        Returns:
            x509.Certificate object
        """
        now = datetime.utcnow()
        
        # Key usage for end entity
        ku = x509.KeyUsage(
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
        
        # Extended key usage based on cert type
        if cert_type == 'SERVICE':
            eku = x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.SERVER_AUTH,
                ExtendedKeyUsageOID.CLIENT_AUTH,
            ])
        else:
            eku = x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.CLIENT_AUTH,
                ExtendedKeyUsageOID.EMAIL_PROTECTION,
                ExtendedKeyUsageOID.CODE_SIGNING,  # For document signing
            ])
        
        # Basic constraints (not a CA)
        bc = x509.BasicConstraints(ca=False, path_length=None)
        
        # Subject Key Identifier
        ski = x509.SubjectKeyIdentifier.from_public_key(csr.public_key())
        
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(csr.subject)
        builder = builder.issuer_name(issuer_cert.subject)
        builder = builder.public_key(csr.public_key())
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.not_valid_before(now)
        builder = builder.not_valid_after(now + timedelta(days=validity_days))
        builder = builder.add_extension(bc, critical=True)
        builder = builder.add_extension(ku, critical=True)
        builder = builder.add_extension(eku, critical=False)
        builder = builder.add_extension(ski, critical=False)
        
        # Authority Key Identifier
        try:
            issuer_ski = issuer_cert.extensions.get_extension_for_class(
                x509.SubjectKeyIdentifier
            )
            aki = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                issuer_ski.value
            )
            builder = builder.add_extension(aki, critical=False)
        except x509.ExtensionNotFound:
            pass
        
        # Sign the certificate
        certificate = builder.sign(issuer_key, hashes.SHA384(), default_backend())
        
        return certificate
    
    @classmethod
    def create_csr(cls, private_key, common_name, organization=None,
                   organizational_unit=None, country='VN', email=None):
        """
        Create a Certificate Signing Request.
        
        Args:
            private_key: Private key for the CSR
            common_name: Subject CN
            organization: Subject O
            organizational_unit: Subject OU
            country: Subject C
            email: Email address
            
        Returns:
            x509.CertificateSigningRequest
        """
        name_attrs = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        
        if organization:
            name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
        if organizational_unit:
            name_attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit))
        if country:
            name_attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
        if email:
            name_attrs.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))
        
        subject = x509.Name(name_attrs)
        
        builder = x509.CertificateSigningRequestBuilder()
        builder = builder.subject_name(subject)
        
        csr = builder.sign(private_key, hashes.SHA384(), default_backend())
        return csr
    
    @classmethod
    def serialize_certificate(cls, certificate):
        """
        Serialize certificate to PEM format.
        
        Args:
            certificate: x509.Certificate object
            
        Returns:
            bytes: PEM-encoded certificate
        """
        return certificate.public_bytes(serialization.Encoding.PEM)
    
    @classmethod
    def load_certificate(cls, pem_data):
        """
        Load certificate from PEM format.
        
        Args:
            pem_data: PEM-encoded certificate
            
        Returns:
            x509.Certificate object
        """
        if isinstance(pem_data, str):
            pem_data = pem_data.encode()
        
        return x509.load_pem_x509_certificate(pem_data, default_backend())
    
    @classmethod
    def get_certificate_fingerprint(cls, certificate, algorithm='sha256'):
        """
        Get certificate fingerprint.
        
        Args:
            certificate: x509.Certificate or PEM bytes
            algorithm: Hash algorithm (sha256, sha1)
            
        Returns:
            str: Hex-encoded fingerprint
        """
        if isinstance(certificate, bytes):
            certificate = cls.load_certificate(certificate)
        
        if algorithm == 'sha256':
            hash_algo = hashes.SHA256()
        else:
            hash_algo = hashes.SHA1()
        
        return certificate.fingerprint(hash_algo).hex().upper()
    
    @classmethod
    def build_subject_name(cls, common_name, organization=None,
                          organizational_unit=None, locality=None,
                          state=None, country='VN', email=None):
        """
        Build an X.509 subject name.
        
        Returns:
            x509.Name object
        """
        attrs = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        
        if organizational_unit:
            attrs.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, organizational_unit))
        if organization:
            attrs.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
        if locality:
            attrs.append(x509.NameAttribute(NameOID.LOCALITY_NAME, locality))
        if state:
            attrs.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state))
        if country:
            attrs.append(x509.NameAttribute(NameOID.COUNTRY_NAME, country))
        if email:
            attrs.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))
        
        return x509.Name(attrs)
