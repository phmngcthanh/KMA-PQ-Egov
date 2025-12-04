"""
Certificate Authority Models

Defines the CA hierarchy for the e-government PKI system:
- Root CA: Top-level trust anchor
- Intermediate CAs: For officers, citizens, and services
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid


class CertificateAuthority(models.Model):
    """
    Certificate Authority model supporting both classical and post-quantum cryptography.
    
    Implements a hierarchical CA structure:
    - ROOT: Self-signed root CA (offline, highly protected)
    - INTERMEDIATE_OFFICER: Issues certificates to government officers
    - INTERMEDIATE_CITIZEN: Issues certificates to citizens
    - INTERMEDIATE_SERVICE: Issues certificates for system services
    """
    
    CA_TYPES = [
        ('ROOT', 'Root CA'),
        ('INTERMEDIATE_OFFICER', 'Officer Intermediate CA'),
        ('INTERMEDIATE_CITIZEN', 'Citizen Intermediate CA'),
        ('INTERMEDIATE_SERVICE', 'Service Intermediate CA'),
    ]
    
    KEY_ALGORITHMS = [
        ('RSA_2048', 'RSA 2048-bit'),
        ('RSA_4096', 'RSA 4096-bit'),
        ('ECDSA_P256', 'ECDSA P-256'),
        ('ECDSA_P384', 'ECDSA P-384'),
    ]
    
    PQ_ALGORITHMS = [
        ('NONE', 'No Post-Quantum'),
        ('DILITHIUM2', 'Dilithium2 (ML-DSA-44)'),
        ('DILITHIUM3', 'Dilithium3 (ML-DSA-65)'),
        ('DILITHIUM5', 'Dilithium5 (ML-DSA-87)'),
        ('FALCON512', 'Falcon-512'),
        ('FALCON1024', 'Falcon-1024'),
        ('SPHINCS_SHA2_128F', 'SPHINCS+-SHA2-128f'),
    ]
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # CA Identity
    name = models.CharField(max_length=255, unique=True, 
                           help_text="Friendly name for the CA")
    common_name = models.CharField(max_length=255,
                                   help_text="CN field in certificate subject")
    organization = models.CharField(max_length=255, default="E-Government PKI")
    organizational_unit = models.CharField(max_length=255, blank=True)
    locality = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, default='VN')
    email = models.EmailField(blank=True)
    
    # CA Type and Hierarchy
    ca_type = models.CharField(max_length=30, choices=CA_TYPES)
    parent_ca = models.ForeignKey(
        'self', 
        null=True, 
        blank=True,
        on_delete=models.PROTECT,
        related_name='subordinate_cas',
        help_text="Parent CA (null for Root CA)"
    )
    path_length = models.IntegerField(
        default=0,
        help_text="Maximum path length for subordinate CAs"
    )
    
    # Classical Cryptography (RSA/ECDSA)
    key_algorithm = models.CharField(
        max_length=20, 
        choices=KEY_ALGORITHMS, 
        default='RSA_4096'
    )
    certificate_pem = models.TextField(
        help_text="X.509 certificate in PEM format"
    )
    private_key_pem_encrypted = models.BinaryField(
        help_text="Encrypted private key (AES-256-GCM)"
    )
    public_key_pem = models.TextField(
        help_text="Public key in PEM format"
    )
    
    # Post-Quantum Cryptography
    pq_algorithm = models.CharField(
        max_length=30,
        choices=PQ_ALGORITHMS,
        default='DILITHIUM3',
        help_text="Post-quantum signature algorithm"
    )
    pq_public_key = models.BinaryField(
        null=True, 
        blank=True,
        help_text="Post-quantum public key bytes"
    )
    pq_private_key_encrypted = models.BinaryField(
        null=True, 
        blank=True,
        help_text="Encrypted post-quantum private key"
    )
    
    # Certificate Details
    serial_number = models.CharField(
        max_length=64, 
        unique=True,
        help_text="Certificate serial number (hex)"
    )
    valid_from = models.DateTimeField(help_text="Certificate not valid before")
    valid_until = models.DateTimeField(help_text="Certificate not valid after")
    
    # Key Usage and Extended Key Usage
    key_usage = models.JSONField(
        default=list,
        help_text="X.509 Key Usage extensions"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_compromised = models.BooleanField(
        default=False,
        help_text="Set to True if CA key is compromised"
    )
    
    # CRL Configuration
    crl_distribution_point = models.URLField(
        blank=True,
        help_text="URL where CRL can be downloaded"
    )
    ocsp_responder_url = models.URLField(
        blank=True,
        help_text="URL of OCSP responder"
    )
    crl_validity_days = models.IntegerField(
        default=7,
        help_text="Number of days CRL is valid"
    )
    next_crl_update = models.DateTimeField(null=True, blank=True)
    last_crl_number = models.IntegerField(default=0)
    
    # Certificate issuance settings
    max_cert_validity_days = models.IntegerField(
        default=365,
        help_text="Maximum validity period for issued certificates"
    )
    certificates_issued = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Certificate Authority"
        verbose_name_plural = "Certificate Authorities"
        ordering = ['ca_type', 'name']
    
    def __str__(self):
        return f"{self.get_ca_type_display()}: {self.name}"
    
    def is_root_ca(self):
        """Check if this is a root CA"""
        return self.ca_type == 'ROOT'
    
    def is_valid(self):
        """Check if CA certificate is currently valid"""
        now = timezone.now()
        return (
            self.is_active and 
            not self.is_compromised and
            self.valid_from <= now <= self.valid_until
        )
    
    def get_certificate_chain(self):
        """Get the certificate chain from this CA to root"""
        chain = [self]
        current = self
        while current.parent_ca:
            current = current.parent_ca
            chain.append(current)
        return chain
    
    def get_next_serial_number(self):
        """Generate the next serial number for certificate issuance"""
        self.certificates_issued += 1
        self.save(update_fields=['certificates_issued'])
        # Format: CA_ID prefix + timestamp + sequence
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        return f"{str(self.id)[:8]}{timestamp}{self.certificates_issued:06d}"
    
    def needs_crl_update(self):
        """Check if CRL needs to be regenerated"""
        if self.next_crl_update is None:
            return True
        return timezone.now() >= self.next_crl_update
    
    def can_issue_certificate(self, cert_type):
        """Check if this CA can issue a specific certificate type"""
        if not self.is_valid():
            return False
        
        type_mapping = {
            'OFFICER': 'INTERMEDIATE_OFFICER',
            'CITIZEN': 'INTERMEDIATE_CITIZEN',
            'SERVICE': 'INTERMEDIATE_SERVICE',
        }
        
        return self.ca_type == type_mapping.get(cert_type)
    
    @property
    def subject_dn(self):
        """Build the subject distinguished name"""
        parts = []
        if self.common_name:
            parts.append(f"CN={self.common_name}")
        if self.organizational_unit:
            parts.append(f"OU={self.organizational_unit}")
        if self.organization:
            parts.append(f"O={self.organization}")
        if self.locality:
            parts.append(f"L={self.locality}")
        if self.state:
            parts.append(f"ST={self.state}")
        if self.country:
            parts.append(f"C={self.country}")
        return ", ".join(parts)
