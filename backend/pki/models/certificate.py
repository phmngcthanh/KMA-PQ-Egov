"""
User Certificate Models

Defines certificates issued to users (officers, citizens, services)
and certificate signing requests (CSR).
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import hashlib


class CertificateRequest(models.Model):
    """
    Certificate Signing Request (CSR) from users.
    
    Users submit a CSR which is reviewed and approved by administrators
    before a certificate is issued.
    """
    
    REQUEST_STATUS = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ISSUED', 'Certificate Issued'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    CERT_TYPES = [
        ('OFFICER', 'Government Officer'),
        ('CITIZEN', 'Citizen'),
        ('SERVICE', 'Service Account'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Requester
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificate_requests'
    )
    
    # Request details
    cert_type = models.CharField(max_length=20, choices=CERT_TYPES)
    common_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, blank=True)
    organizational_unit = models.CharField(max_length=255, blank=True)
    
    # For officer certificates - additional verification
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=255, blank=True)
    
    # For citizen certificates - identity verification
    citizen_id = models.CharField(max_length=20, blank=True,
                                  help_text="CMND/CCCD number")
    
    # CSR data (generated client-side, private key stays with user)
    csr_pem = models.TextField(
        blank=True,
        help_text="PKCS#10 Certificate Signing Request in PEM format"
    )
    
    # Request for post-quantum certificate
    include_pq = models.BooleanField(
        default=True,
        help_text="Include post-quantum key in certificate"
    )
    pq_public_key = models.BinaryField(
        null=True, 
        blank=True,
        help_text="User's post-quantum public key"
    )
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=REQUEST_STATUS, 
        default='PENDING'
    )
    
    # Review
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_cert_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Resulting certificate
    issued_certificate = models.OneToOneField(
        'UserCertificate',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='source_request'
    )
    
    # Validity request
    requested_validity_days = models.IntegerField(
        default=365,
        help_text="Requested certificate validity in days"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Certificate Request"
        verbose_name_plural = "Certificate Requests"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"CSR-{str(self.id)[:8]} ({self.user.email})"
    
    def approve(self, reviewer):
        """Approve the certificate request"""
        self.status = 'APPROVED'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject(self, reviewer, reason):
        """Reject the certificate request"""
        self.status = 'REJECTED'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class UserCertificate(models.Model):
    """
    Digital certificate issued to a user.
    
    Supports hybrid certificates with both classical (RSA/ECDSA) 
    and post-quantum (Dilithium) signatures.
    """
    
    CERT_TYPES = [
        ('OFFICER', 'Government Officer'),
        ('CITIZEN', 'Citizen'),
        ('SERVICE', 'Service Account'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('REVOKED', 'Revoked'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('PENDING_ACTIVATION', 'Pending Activation'),
    ]
    
    KEY_ALGORITHMS = [
        ('RSA_2048', 'RSA 2048-bit'),
        ('RSA_4096', 'RSA 4096-bit'),
        ('ECDSA_P256', 'ECDSA P-256'),
        ('ECDSA_P384', 'ECDSA P-384'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Owner
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    
    # Issuing CA
    issuing_ca = models.ForeignKey(
        'CertificateAuthority',
        on_delete=models.PROTECT,
        related_name='issued_certificates'
    )
    
    # Certificate type
    cert_type = models.CharField(max_length=20, choices=CERT_TYPES)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='PENDING_ACTIVATION'
    )
    
    # Certificate Identity
    serial_number = models.CharField(max_length=64, unique=True)
    subject_dn = models.CharField(
        max_length=500,
        help_text="Full subject distinguished name"
    )
    
    # Classical Certificate (X.509)
    key_algorithm = models.CharField(
        max_length=20,
        choices=KEY_ALGORITHMS,
        default='RSA_4096'
    )
    certificate_pem = models.TextField(
        help_text="X.509 certificate in PEM format"
    )
    public_key_pem = models.TextField(
        help_text="Public key in PEM format"
    )
    
    # Post-Quantum Components
    has_pq_key = models.BooleanField(
        default=True,
        help_text="Certificate includes post-quantum key"
    )
    pq_algorithm = models.CharField(
        max_length=30,
        default='DILITHIUM3'
    )
    pq_public_key = models.BinaryField(
        null=True, 
        blank=True,
        help_text="Post-quantum public key"
    )
    pq_certificate_extension = models.TextField(
        blank=True,
        help_text="PQ key embedded as X.509 extension (base64)"
    )
    
    # Hybrid Signature (both classical and PQ)
    hybrid_signature = models.BinaryField(
        null=True,
        blank=True,
        help_text="Combined classical + PQ signature over certificate"
    )
    
    # Validity Period
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Fingerprints
    fingerprint_sha256 = models.CharField(
        max_length=64,
        help_text="SHA-256 fingerprint of certificate"
    )
    fingerprint_sha1 = models.CharField(
        max_length=40,
        blank=True,
        help_text="SHA-1 fingerprint (for legacy compatibility)"
    )
    
    # Key Usage
    key_usage = models.JSONField(
        default=list,
        help_text="X.509 Key Usage flags"
    )
    extended_key_usage = models.JSONField(
        default=list,
        help_text="X.509 Extended Key Usage OIDs"
    )
    
    # Revocation
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=50, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='revoked_certificates'
    )
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Certificate"
        verbose_name_plural = "User Certificates"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['fingerprint_sha256']),
        ]
    
    def __str__(self):
        return f"CERT-{self.serial_number[:12]} ({self.user.email})"
    
    def is_valid(self):
        """Check if certificate is currently valid"""
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and
            self.valid_from <= now <= self.valid_until
        )
    
    def is_expired(self):
        """Check if certificate has expired"""
        return timezone.now() > self.valid_until
    
    def days_until_expiry(self):
        """Get number of days until certificate expires"""
        delta = self.valid_until - timezone.now()
        return max(0, delta.days)
    
    def revoke(self, reason, revoked_by=None):
        """Revoke the certificate"""
        self.status = 'REVOKED'
        self.revoked_at = timezone.now()
        self.revocation_reason = reason
        self.revoked_by = revoked_by
        self.save()
    
    def record_usage(self):
        """Record certificate usage"""
        self.last_used_at = timezone.now()
        self.usage_count += 1
        self.save(update_fields=['last_used_at', 'usage_count'])
    
    def get_certificate_chain_pem(self):
        """Get full certificate chain in PEM format"""
        chain = [self.certificate_pem]
        current_ca = self.issuing_ca
        while current_ca:
            chain.append(current_ca.certificate_pem)
            current_ca = current_ca.parent_ca
        return '\n'.join(chain)
    
    @staticmethod
    def compute_fingerprint(cert_der):
        """Compute SHA-256 fingerprint of certificate"""
        return hashlib.sha256(cert_der).hexdigest().upper()
    
    def can_sign_documents(self):
        """Check if certificate can be used for document signing"""
        return (
            self.is_valid() and
            'digitalSignature' in self.key_usage
        )
    
    def can_authenticate(self):
        """Check if certificate can be used for authentication"""
        return (
            self.is_valid() and
            ('clientAuth' in self.extended_key_usage or
             'digitalSignature' in self.key_usage)
        )
