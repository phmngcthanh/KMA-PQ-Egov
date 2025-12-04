"""
PKI Audit Log Model

Comprehensive audit logging for all PKI operations.
Required for compliance and security monitoring.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import json


class PKIAuditLog(models.Model):
    """
    Audit log for PKI operations.
    
    Records all significant PKI events for security monitoring,
    compliance reporting, and forensic analysis.
    """
    
    EVENT_TYPES = [
        # CA Events
        ('CA_CREATED', 'CA Created'),
        ('CA_UPDATED', 'CA Updated'),
        ('CA_DEACTIVATED', 'CA Deactivated'),
        ('CA_KEY_CEREMONY', 'CA Key Ceremony'),
        
        # Certificate Events
        ('CERT_REQUESTED', 'Certificate Requested'),
        ('CERT_REQUEST_APPROVED', 'Certificate Request Approved'),
        ('CERT_REQUEST_REJECTED', 'Certificate Request Rejected'),
        ('CERT_ISSUED', 'Certificate Issued'),
        ('CERT_REVOKED', 'Certificate Revoked'),
        ('CERT_SUSPENDED', 'Certificate Suspended'),
        ('CERT_RENEWED', 'Certificate Renewed'),
        ('CERT_DOWNLOADED', 'Certificate Downloaded'),
        
        # CRL/OCSP Events
        ('CRL_GENERATED', 'CRL Generated'),
        ('CRL_PUBLISHED', 'CRL Published'),
        ('OCSP_RESPONSE', 'OCSP Response Generated'),
        
        # Signing Events
        ('DOCUMENT_SIGNED', 'Document Signed'),
        ('SIGNATURE_VERIFIED', 'Signature Verified'),
        ('SIGNATURE_INVALID', 'Invalid Signature Detected'),
        
        # Authentication Events
        ('CERT_AUTH_SUCCESS', 'Certificate Authentication Success'),
        ('CERT_AUTH_FAILURE', 'Certificate Authentication Failure'),
        
        # Key Events
        ('KEY_GENERATED', 'Key Pair Generated'),
        ('KEY_EXPORTED', 'Key Exported'),
        ('KEY_IMPORTED', 'Key Imported'),
        
        # System Events
        ('CONFIG_CHANGED', 'Configuration Changed'),
        ('SYSTEM_ERROR', 'System Error'),
    ]
    
    SEVERITY_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Event Classification
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(
        max_length=10, 
        choices=SEVERITY_LEVELS,
        default='INFO'
    )
    
    # Actor Information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='pki_audit_logs'
    )
    user_email = models.EmailField(
        blank=True,
        help_text="Preserved email in case user is deleted"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # Target Objects
    ca_id = models.UUIDField(null=True, blank=True)
    ca_name = models.CharField(max_length=255, blank=True)
    certificate_id = models.UUIDField(null=True, blank=True)
    certificate_serial = models.CharField(max_length=64, blank=True)
    
    # Event Details
    description = models.TextField(
        help_text="Human-readable description of the event"
    )
    details = models.JSONField(
        default=dict,
        help_text="Additional event details"
    )
    
    # Request/Response Data (for debugging)
    request_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sanitized request data"
    )
    response_status = models.CharField(max_length=20, blank=True)
    
    # Success/Failure
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Cryptographic integrity
    event_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of event data for integrity"
    )
    previous_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hash of previous log entry (chain integrity)"
    )
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = "PKI Audit Log"
        verbose_name_plural = "PKI Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['certificate_id']),
            models.Index(fields=['ca_id']),
        ]
    
    def __str__(self):
        return f"[{self.timestamp}] {self.get_event_type_display()}"
    
    def save(self, *args, **kwargs):
        # Preserve user email
        if self.user and not self.user_email:
            self.user_email = self.user.email
        
        # Calculate event hash for integrity
        if not self.event_hash:
            self.event_hash = self._calculate_hash()
        
        super().save(*args, **kwargs)
    
    def _calculate_hash(self):
        """Calculate SHA-256 hash of event data"""
        import hashlib
        data = {
            'event_type': self.event_type,
            'timestamp': str(self.timestamp),
            'user_email': self.user_email,
            'description': self.description,
            'details': self.details,
            'previous_hash': self.previous_hash,
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    @classmethod
    def log(cls, event_type, description, user=None, request=None, 
            ca=None, certificate=None, severity='INFO', success=True,
            error_message='', details=None):
        """
        Create a new audit log entry.
        
        Args:
            event_type: One of EVENT_TYPES
            description: Human-readable description
            user: The user performing the action
            request: HTTP request object (for IP, user agent)
            ca: CertificateAuthority instance
            certificate: UserCertificate instance
            severity: Log severity level
            success: Whether the operation succeeded
            error_message: Error message if failed
            details: Additional details dict
        """
        # Get previous hash for chain integrity
        last_log = cls.objects.order_by('-timestamp').first()
        previous_hash = last_log.event_hash if last_log else ''
        
        log_entry = cls(
            event_type=event_type,
            severity=severity,
            user=user,
            description=description,
            success=success,
            error_message=error_message,
            details=details or {},
            previous_hash=previous_hash,
        )
        
        # Extract request info
        if request:
            log_entry.ip_address = cls._get_client_ip(request)
            log_entry.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # CA info
        if ca:
            log_entry.ca_id = ca.id
            log_entry.ca_name = ca.name
        
        # Certificate info
        if certificate:
            log_entry.certificate_id = certificate.id
            log_entry.certificate_serial = certificate.serial_number
        
        log_entry.save()
        return log_entry
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
