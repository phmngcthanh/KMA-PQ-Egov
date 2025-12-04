"""
PKI Serializers

Django REST Framework serializers for PKI operations.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CertificateAuthority,
    UserCertificate,
    CertificateRequest,
    RevokedCertificate,
    CRL,
    PKIAuditLog,
)

User = get_user_model()


class CertificateAuthoritySerializer(serializers.ModelSerializer):
    """Serializer for Certificate Authority."""
    
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    certificate_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CertificateAuthority
        fields = [
            'id', 'name', 'description', 'ca_type', 'parent', 'parent_name',
            'key_algorithm', 'pq_algorithm', 'certificate_pem',
            'valid_from', 'valid_until', 'is_active',
            'crl_distribution_point', 'ocsp_responder_url',
            'certificate_count', 'created_at',
        ]
        read_only_fields = [
            'id', 'certificate_pem', 'valid_from', 'valid_until',
            'created_at', 'certificate_count',
        ]


class CertificateAuthorityCreateSerializer(serializers.Serializer):
    """Serializer for creating a new CA."""
    
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    ca_type = serializers.ChoiceField(choices=['ROOT', 'INTERMEDIATE'])
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Subject fields
    country = serializers.CharField(max_length=2, default='VN')
    state = serializers.CharField(max_length=128, required=False)
    locality = serializers.CharField(max_length=128, required=False)
    organization = serializers.CharField(max_length=255)
    organizational_unit = serializers.CharField(max_length=255, required=False)
    
    # Key parameters
    key_algorithm = serializers.ChoiceField(
        choices=['RSA-2048', 'RSA-4096', 'ECDSA-P256', 'ECDSA-P384'],
        default='RSA-4096'
    )
    pq_algorithm = serializers.ChoiceField(
        choices=['DILITHIUM2', 'DILITHIUM3', 'DILITHIUM5', 'FALCON-512', 'FALCON-1024'],
        default='DILITHIUM3'
    )
    
    # Validity
    validity_days = serializers.IntegerField(default=3650, min_value=365)
    
    def validate(self, data):
        """Validate CA creation data."""
        if data['ca_type'] == 'ROOT' and data.get('parent_id'):
            raise serializers.ValidationError(
                "Root CA cannot have a parent."
            )
        if data['ca_type'] == 'INTERMEDIATE' and not data.get('parent_id'):
            raise serializers.ValidationError(
                "Intermediate CA must have a parent."
            )
        
        if data.get('parent_id'):
            try:
                parent = CertificateAuthority.objects.get(
                    id=data['parent_id'],
                    is_active=True
                )
                data['parent'] = parent
            except CertificateAuthority.DoesNotExist:
                raise serializers.ValidationError(
                    "Parent CA not found or not active."
                )
        
        return data


class UserCertificateSerializer(serializers.ModelSerializer):
    """Serializer for user certificates."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    ca_name = serializers.CharField(source='issuing_ca.name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    is_revoked = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserCertificate
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'certificate_type', 'serial_number', 'fingerprint',
            'issuing_ca', 'ca_name',
            'key_algorithm', 'pq_algorithm',
            'certificate_pem', 'pq_certificate_data',
            'valid_from', 'valid_until',
            'is_valid', 'is_revoked', 'revocation_date', 'revocation_reason',
            'created_at',
        ]
        read_only_fields = [
            'id', 'serial_number', 'fingerprint', 'certificate_pem',
            'pq_certificate_data', 'valid_from', 'valid_until',
            'is_valid', 'is_revoked', 'revocation_date', 'revocation_reason',
            'created_at',
        ]
    
    def get_user_name(self, obj):
        """Get user's full name or email."""
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.email


class CertificateRequestSerializer(serializers.ModelSerializer):
    """Serializer for certificate requests."""
    
    requester_email = serializers.EmailField(source='user.email', read_only=True)
    requester_name = serializers.SerializerMethodField()
    approver_email = serializers.EmailField(source='approved_by.email', read_only=True)
    
    class Meta:
        model = CertificateRequest
        fields = [
            'id', 'user', 'requester_email', 'requester_name',
            'certificate_type', 'status',
            'key_algorithm', 'pq_algorithm',
            'csr_pem', 'common_name', 'email', 'organization',
            'organizational_unit', 'country', 'state', 'locality',
            'approved_by', 'approver_email', 'approved_at',
            'rejection_reason', 'issued_certificate',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user', 'status', 'approved_by', 'approved_at',
            'rejection_reason', 'issued_certificate',
            'created_at', 'updated_at',
        ]
    
    def get_requester_name(self, obj):
        """Get requester's full name or email."""
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.email


class CertificateRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating certificate requests."""
    
    certificate_type = serializers.ChoiceField(choices=['OFFICER', 'CITIZEN'])
    
    # Subject info (optional - will use user info if not provided)
    common_name = serializers.CharField(max_length=255, required=False)
    organization = serializers.CharField(max_length=255, required=False)
    organizational_unit = serializers.CharField(max_length=255, required=False)
    country = serializers.CharField(max_length=2, default='VN')
    state = serializers.CharField(max_length=128, required=False)
    locality = serializers.CharField(max_length=128, required=False)
    
    # Key parameters
    key_algorithm = serializers.ChoiceField(
        choices=['RSA-2048', 'RSA-4096', 'ECDSA-P256'],
        default='RSA-4096'
    )
    pq_algorithm = serializers.ChoiceField(
        choices=['DILITHIUM2', 'DILITHIUM3', 'DILITHIUM5'],
        default='DILITHIUM3'
    )


class CertificateApprovalSerializer(serializers.Serializer):
    """Serializer for approving certificate requests."""
    
    request_id = serializers.IntegerField()
    ca_id = serializers.IntegerField()
    validity_days = serializers.IntegerField(default=365, min_value=30, max_value=3650)
    
    def validate_request_id(self, value):
        """Validate that request exists and is pending."""
        try:
            request = CertificateRequest.objects.get(id=value)
            if request.status != 'PENDING':
                raise serializers.ValidationError(
                    f"Request is not pending. Current status: {request.status}"
                )
            return value
        except CertificateRequest.DoesNotExist:
            raise serializers.ValidationError("Certificate request not found.")
    
    def validate_ca_id(self, value):
        """Validate that CA exists and is active."""
        try:
            ca = CertificateAuthority.objects.get(id=value, is_active=True)
            return value
        except CertificateAuthority.DoesNotExist:
            raise serializers.ValidationError("CA not found or not active.")


class CertificateRejectionSerializer(serializers.Serializer):
    """Serializer for rejecting certificate requests."""
    
    request_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=1000)
    
    def validate_request_id(self, value):
        """Validate that request exists and is pending."""
        try:
            request = CertificateRequest.objects.get(id=value)
            if request.status != 'PENDING':
                raise serializers.ValidationError(
                    f"Request is not pending. Current status: {request.status}"
                )
            return value
        except CertificateRequest.DoesNotExist:
            raise serializers.ValidationError("Certificate request not found.")


class CertificateRevocationSerializer(serializers.Serializer):
    """Serializer for revoking certificates."""
    
    certificate_id = serializers.IntegerField()
    reason = serializers.ChoiceField(
        choices=[
            'unspecified',
            'key_compromise',
            'ca_compromise',
            'affiliation_changed',
            'superseded',
            'cessation_of_operation',
            'certificate_hold',
            'privilege_withdrawn',
        ],
        default='unspecified'
    )
    reason_text = serializers.CharField(max_length=1000, required=False)
    
    def validate_certificate_id(self, value):
        """Validate that certificate exists and is not revoked."""
        try:
            cert = UserCertificate.objects.get(id=value)
            if cert.revocation_date:
                raise serializers.ValidationError("Certificate is already revoked.")
            return value
        except UserCertificate.DoesNotExist:
            raise serializers.ValidationError("Certificate not found.")


class RevokedCertificateSerializer(serializers.ModelSerializer):
    """Serializer for revoked certificates."""
    
    certificate_serial = serializers.CharField(
        source='certificate.serial_number', read_only=True
    )
    
    class Meta:
        model = RevokedCertificate
        fields = [
            'id', 'crl', 'certificate', 'certificate_serial',
            'serial_number', 'revocation_date', 'reason',
        ]
        read_only_fields = ['id', 'revocation_date']


class CRLSerializer(serializers.ModelSerializer):
    """Serializer for CRLs."""
    
    ca_name = serializers.CharField(source='issuing_ca.name', read_only=True)
    revoked_count = serializers.IntegerField(source='entries_count', read_only=True)
    
    class Meta:
        model = CRL
        fields = [
            'id', 'issuing_ca', 'ca_name', 'crl_number',
            'this_update', 'next_update', 'crl_pem',
            'revoked_count', 'created_at',
        ]
        read_only_fields = ['id', 'crl_number', 'this_update', 'crl_pem', 'created_at']


class PKIAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs."""
    
    actor_email = serializers.EmailField(source='actor.email', read_only=True)
    
    class Meta:
        model = PKIAuditLog
        fields = [
            'id', 'timestamp', 'actor', 'actor_email',
            'action', 'resource_type', 'resource_id',
            'details', 'ip_address', 'user_agent',
            'success', 'error_message',
        ]
        read_only_fields = ['id', 'timestamp']


# ============ Authentication Serializers ============

class ChallengeRequestSerializer(serializers.Serializer):
    """Serializer for requesting an auth challenge."""
    
    email = serializers.EmailField()
    certificate_fingerprint = serializers.CharField(max_length=128)


class ChallengeResponseSerializer(serializers.Serializer):
    """Serializer for responding to an auth challenge."""
    
    challenge_id = serializers.CharField(max_length=64)
    classical_signature = serializers.CharField()  # Base64 encoded
    pq_signature = serializers.CharField(required=False)  # Base64 encoded


class CertificateLoginSerializer(serializers.Serializer):
    """Serializer for certificate-based login (via TLS client cert)."""
    
    # The certificate is extracted from request headers by middleware
    # This serializer is used for additional validation if needed
    pass


class CertificateDownloadSerializer(serializers.Serializer):
    """Serializer for certificate download options."""
    
    certificate_id = serializers.IntegerField()
    format = serializers.ChoiceField(
        choices=['pem', 'der', 'p12', 'pkcs12'],
        default='pem'
    )
    include_private_key = serializers.BooleanField(default=False)
    password = serializers.CharField(
        required=False,
        min_length=8,
        help_text="Required if include_private_key is True"
    )
    
    def validate(self, data):
        """Validate download options."""
        if data.get('include_private_key') and not data.get('password'):
            raise serializers.ValidationError(
                "Password is required when including private key."
            )
        return data


# ============ PDF Signing Serializers ============

class PDFSignSerializer(serializers.Serializer):
    """Serializer for PDF signing requests."""
    
    certificate_id = serializers.IntegerField()
    signature_reason = serializers.CharField(max_length=255, required=False)
    signature_location = serializers.CharField(max_length=255, required=False)
    signature_contact = serializers.CharField(max_length=255, required=False)
    
    # For challenge-response signing
    challenge_id = serializers.CharField(max_length=64, required=False)
    classical_signature = serializers.CharField(required=False)
    pq_signature = serializers.CharField(required=False)
    
    def validate_certificate_id(self, value):
        """Validate that certificate exists and is valid."""
        try:
            cert = UserCertificate.objects.get(id=value)
            if not cert.is_valid:
                raise serializers.ValidationError("Certificate is not valid.")
            return value
        except UserCertificate.DoesNotExist:
            raise serializers.ValidationError("Certificate not found.")


class PDFVerifySerializer(serializers.Serializer):
    """Serializer for PDF signature verification requests."""
    
    # PDF file is uploaded as multipart form data
    verify_pq_signature = serializers.BooleanField(default=True)


class PDFSignatureResultSerializer(serializers.Serializer):
    """Serializer for PDF signature verification results."""
    
    is_valid = serializers.BooleanField()
    signer_name = serializers.CharField()
    signer_email = serializers.CharField()
    certificate_serial = serializers.CharField()
    signing_time = serializers.DateTimeField()
    signature_reason = serializers.CharField(required=False)
    signature_location = serializers.CharField(required=False)
    
    # Classical signature status
    classical_signature_valid = serializers.BooleanField()
    classical_algorithm = serializers.CharField()
    
    # Post-quantum signature status
    pq_signature_present = serializers.BooleanField()
    pq_signature_valid = serializers.BooleanField(required=False)
    pq_algorithm = serializers.CharField(required=False)
    
    # Certificate chain validation
    chain_valid = serializers.BooleanField()
    chain_errors = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    # Revocation status
    revocation_checked = serializers.BooleanField()
    is_revoked = serializers.BooleanField(required=False)
