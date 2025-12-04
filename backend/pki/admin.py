"""
PKI Admin Configuration

Django admin interface for PKI models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    CertificateAuthority,
    UserCertificate,
    CertificateRequest,
    RevokedCertificate,
    CRL,
    OCSPResponse,
    PKIAuditLog,
)


@admin.register(CertificateAuthority)
class CertificateAuthorityAdmin(admin.ModelAdmin):
    """Admin for Certificate Authority model."""
    
    list_display = [
        'name', 'ca_type', 'parent', 'key_algorithm', 'pq_algorithm',
        'is_active', 'valid_until', 'status_badge'
    ]
    list_filter = ['ca_type', 'is_active', 'key_algorithm', 'pq_algorithm']
    search_fields = ['name', 'description']
    readonly_fields = [
        'certificate_pem', 'pq_public_key', 'valid_from', 'valid_until',
        'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'ca_type', 'parent', 'is_active')
        }),
        ('Cryptography', {
            'fields': ('key_algorithm', 'pq_algorithm')
        }),
        ('Certificate', {
            'fields': ('certificate_pem', 'pq_public_key', 'valid_from', 'valid_until')
        }),
        ('Distribution Points', {
            'fields': ('crl_distribution_point', 'ocsp_responder_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        now = timezone.now()
        if not obj.is_active:
            return format_html('<span style="color: gray;">Inactive</span>')
        if obj.valid_until < now:
            return format_html('<span style="color: red;">Expired</span>')
        if obj.valid_from > now:
            return format_html('<span style="color: orange;">Not Yet Valid</span>')
        return format_html('<span style="color: green;">Valid</span>')
    status_badge.short_description = 'Status'


@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    """Admin for User Certificate model."""
    
    list_display = [
        'serial_number', 'user', 'certificate_type', 'issuing_ca',
        'key_algorithm', 'valid_until', 'status_badge'
    ]
    list_filter = [
        'certificate_type', 'key_algorithm', 'pq_algorithm',
        'issuing_ca', 'revocation_date'
    ]
    search_fields = ['serial_number', 'fingerprint', 'user__email', 'user__username']
    readonly_fields = [
        'serial_number', 'fingerprint', 'certificate_pem', 'pq_certificate_data',
        'valid_from', 'valid_until', 'created_at', 'updated_at'
    ]
    raw_id_fields = ['user', 'issuing_ca']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'certificate_type', 'issuing_ca')
        }),
        ('Identification', {
            'fields': ('serial_number', 'fingerprint')
        }),
        ('Cryptography', {
            'fields': ('key_algorithm', 'pq_algorithm')
        }),
        ('Certificate Data', {
            'fields': ('certificate_pem', 'pq_certificate_data')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Revocation', {
            'fields': ('revocation_date', 'revocation_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status as colored badge."""
        if obj.revocation_date:
            return format_html('<span style="color: red;">Revoked</span>')
        now = timezone.now()
        if obj.valid_until < now:
            return format_html('<span style="color: red;">Expired</span>')
        if obj.valid_from > now:
            return format_html('<span style="color: orange;">Not Yet Valid</span>')
        return format_html('<span style="color: green;">Valid</span>')
    status_badge.short_description = 'Status'


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    """Admin for Certificate Request model."""
    
    list_display = [
        'id', 'user', 'certificate_type', 'status', 'created_at',
        'approved_by', 'approved_at'
    ]
    list_filter = ['status', 'certificate_type', 'key_algorithm']
    search_fields = ['user__email', 'common_name', 'email', 'organization']
    readonly_fields = ['csr_pem', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'approved_by', 'issued_certificate']
    
    fieldsets = (
        ('Requester', {
            'fields': ('user', 'certificate_type', 'status')
        }),
        ('Subject Info', {
            'fields': (
                'common_name', 'email', 'organization',
                'organizational_unit', 'country', 'state', 'locality'
            )
        }),
        ('Cryptography', {
            'fields': ('key_algorithm', 'pq_algorithm', 'csr_pem')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at', 'rejection_reason', 'issued_certificate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Bulk approve pending requests."""
        pending = queryset.filter(status='PENDING')
        count = pending.update(status='APPROVED', approved_by=request.user)
        self.message_user(request, f'{count} requests approved.')
    approve_requests.short_description = 'Approve selected requests'
    
    def reject_requests(self, request, queryset):
        """Bulk reject pending requests."""
        pending = queryset.filter(status='PENDING')
        count = pending.update(status='REJECTED', rejection_reason='Bulk rejected by admin')
        self.message_user(request, f'{count} requests rejected.')
    reject_requests.short_description = 'Reject selected requests'


@admin.register(CRL)
class CRLAdmin(admin.ModelAdmin):
    """Admin for CRL model."""
    
    list_display = ['id', 'issuing_ca', 'crl_number', 'this_update', 'next_update', 'created_at']
    list_filter = ['issuing_ca']
    readonly_fields = ['crl_pem', 'crl_number', 'this_update', 'next_update', 'created_at']
    
    def has_add_permission(self, request):
        """CRLs are generated programmatically."""
        return False


@admin.register(RevokedCertificate)
class RevokedCertificateAdmin(admin.ModelAdmin):
    """Admin for Revoked Certificate model."""
    
    list_display = ['serial_number', 'certificate', 'first_included_in_crl', 'revocation_date', 'reason']
    list_filter = ['reason', 'first_included_in_crl__issuing_ca']
    search_fields = ['serial_number']
    readonly_fields = ['revocation_date']


@admin.register(OCSPResponse)
class OCSPResponseAdmin(admin.ModelAdmin):
    """Admin for OCSP Response model."""
    
    list_display = ['id', 'certificate_serial', 'status', 'this_update', 'next_update']
    list_filter = ['status']
    readonly_fields = ['response_data', 'this_update', 'next_update', 'created_at']


@admin.register(PKIAuditLog)
class PKIAuditLogAdmin(admin.ModelAdmin):
    """Admin for PKI Audit Log model."""
    
    list_display = [
        'timestamp', 'actor', 'action', 'resource_type',
        'resource_id', 'success', 'ip_address'
    ]
    list_filter = ['action', 'resource_type', 'success', 'timestamp']
    search_fields = ['actor__email', 'resource_id', 'ip_address']
    readonly_fields = [
        'timestamp', 'actor', 'action', 'resource_type', 'resource_id',
        'details', 'ip_address', 'user_agent', 'success', 'error_message'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Audit logs are created programmatically."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs should not be deleted."""
        return False
