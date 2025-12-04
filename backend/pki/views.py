"""
PKI API Views

REST API endpoints for PKI operations.
"""

import base64
import os
import tempfile
import logging
from datetime import datetime

from django.http import HttpResponse, FileResponse
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    CertificateAuthority,
    UserCertificate,
    CertificateRequest,
    RevokedCertificate,
    CRL,
    PKIAuditLog,
)
from .serializers import (
    CertificateAuthoritySerializer,
    CertificateAuthorityCreateSerializer,
    UserCertificateSerializer,
    CertificateRequestSerializer,
    CertificateRequestCreateSerializer,
    CertificateApprovalSerializer,
    CertificateRejectionSerializer,
    CertificateRevocationSerializer,
    RevokedCertificateSerializer,
    CRLSerializer,
    PKIAuditLogSerializer,
    ChallengeRequestSerializer,
    ChallengeResponseSerializer,
    CertificateDownloadSerializer,
    PDFSignSerializer,
    PDFVerifySerializer,
    PDFSignatureResultSerializer,
)
from .services import CAService, CertificateService, PDFSigningService
from .auth.backends import ChallengeResponseAuthBackend

User = get_user_model()
logger = logging.getLogger(__name__)


# ============ Permission Classes ============

class IsAdminOrOfficer(permissions.BasePermission):
    """Permission for admin or officer users."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff or getattr(request.user, 'is_officer', False)


class IsCertificateOwner(permissions.BasePermission):
    """Permission for certificate owner."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


# ============ Helper Functions ============

def log_pki_action(request, action, resource_type, resource_id, details=None, 
                   success=True, error_message=None):
    """Create an audit log entry."""
    try:
        PKIAuditLog.objects.create(
            actor=request.user if request.user.is_authenticated else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details or {},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            success=success,
            error_message=error_message,
        )
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ============ CA Views ============

class CertificateAuthorityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Certificate Authority management.
    
    Only admin users can manage CAs.
    """
    queryset = CertificateAuthority.objects.all()
    serializer_class = CertificateAuthoritySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter CAs by type if specified."""
        queryset = super().get_queryset()
        ca_type = self.request.query_params.get('type')
        if ca_type:
            queryset = queryset.filter(ca_type=ca_type.upper())
        return queryset.select_related('parent')
    
    def create(self, request, *args, **kwargs):
        """Create a new Certificate Authority."""
        serializer = CertificateAuthorityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        ca_service = CAService()
        
        try:
            with transaction.atomic():
                if data['ca_type'] == 'ROOT':
                    ca = ca_service.create_root_ca(
                        name=data['name'],
                        subject={
                            'country': data.get('country', 'VN'),
                            'state': data.get('state', ''),
                            'locality': data.get('locality', ''),
                            'organization': data['organization'],
                            'organizational_unit': data.get('organizational_unit', ''),
                            'common_name': data['name'],
                        },
                        key_algorithm=data.get('key_algorithm', 'RSA-4096'),
                        pq_algorithm=data.get('pq_algorithm', 'DILITHIUM3'),
                        validity_days=data.get('validity_days', 3650),
                        description=data.get('description', ''),
                    )
                else:
                    ca = ca_service.create_intermediate_ca(
                        name=data['name'],
                        parent=data['parent'],
                        subject={
                            'country': data.get('country', 'VN'),
                            'state': data.get('state', ''),
                            'locality': data.get('locality', ''),
                            'organization': data['organization'],
                            'organizational_unit': data.get('organizational_unit', ''),
                            'common_name': data['name'],
                        },
                        key_algorithm=data.get('key_algorithm', 'RSA-4096'),
                        pq_algorithm=data.get('pq_algorithm', 'DILITHIUM3'),
                        validity_days=data.get('validity_days', 1825),
                        description=data.get('description', ''),
                    )
                
                log_pki_action(
                    request, 'CREATE_CA', 'CertificateAuthority', ca.id,
                    {'name': ca.name, 'type': ca.ca_type}
                )
                
                return Response(
                    CertificateAuthoritySerializer(ca).data,
                    status=status.HTTP_201_CREATED
                )
        
        except Exception as e:
            log_pki_action(
                request, 'CREATE_CA', 'CertificateAuthority', None,
                {'error': str(e)}, success=False, error_message=str(e)
            )
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def generate_crl(self, request, pk=None):
        """Generate a new CRL for this CA."""
        ca = self.get_object()
        ca_service = CAService()
        
        try:
            crl = ca_service.generate_crl(ca)
            log_pki_action(
                request, 'GENERATE_CRL', 'CRL', crl.id,
                {'ca_id': ca.id, 'crl_number': crl.crl_number}
            )
            return Response(CRLSerializer(crl).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def download_certificate(self, request, pk=None):
        """Download CA certificate."""
        ca = self.get_object()
        format_type = request.query_params.get('format', 'pem')
        
        if format_type == 'pem':
            response = HttpResponse(
                ca.certificate_pem,
                content_type='application/x-pem-file'
            )
            response['Content-Disposition'] = f'attachment; filename="{ca.name}.pem"'
        elif format_type == 'der':
            from cryptography.hazmat.primitives.serialization import Encoding
            from cryptography import x509
            cert = x509.load_pem_x509_certificate(ca.certificate_pem.encode())
            der_data = cert.public_bytes(Encoding.DER)
            response = HttpResponse(
                der_data,
                content_type='application/x-x509-ca-cert'
            )
            response['Content-Disposition'] = f'attachment; filename="{ca.name}.der"'
        else:
            return Response(
                {'error': 'Invalid format. Use pem or der.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return response
    
    @action(detail=True, methods=['get'])
    def chain(self, request, pk=None):
        """Get certificate chain for this CA."""
        ca = self.get_object()
        chain = []
        current = ca
        
        while current:
            chain.append({
                'id': current.id,
                'name': current.name,
                'type': current.ca_type,
                'certificate_pem': current.certificate_pem,
            })
            current = current.parent
        
        return Response({'chain': chain})


# ============ Certificate Views ============

class UserCertificateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User Certificates.
    
    Users can view their own certificates.
    Admins/Officers can view all certificates.
    """
    serializer_class = UserCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter certificates based on user role."""
        user = self.request.user
        queryset = UserCertificate.objects.select_related('user', 'issuing_ca')
        
        if user.is_staff or getattr(user, 'is_officer', False):
            # Admin/Officer can see all
            pass
        else:
            # Regular users only see their own
            queryset = queryset.filter(user=user)
        
        # Filter by status
        valid_only = self.request.query_params.get('valid_only')
        if valid_only:
            now = timezone.now()
            queryset = queryset.filter(
                valid_from__lte=now,
                valid_until__gte=now,
                revocation_date__isnull=True
            )
        
        return queryset
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['revoke', 'revoke_bulk']:
            return [IsAdminOrOfficer()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke a certificate."""
        cert = self.get_object()
        serializer = CertificateRevocationSerializer(data={
            'certificate_id': cert.id,
            **request.data
        })
        serializer.is_valid(raise_exception=True)
        
        cert_service = CertificateService()
        
        try:
            cert_service.revoke_certificate(
                cert,
                reason=serializer.validated_data.get('reason', 'unspecified'),
                revoked_by=request.user
            )
            
            log_pki_action(
                request, 'REVOKE_CERTIFICATE', 'UserCertificate', cert.id,
                {'serial': cert.serial_number, 'reason': serializer.validated_data.get('reason')}
            )
            
            return Response({'status': 'Certificate revoked successfully.'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download certificate in various formats."""
        cert = self.get_object()
        
        # Check ownership
        if not request.user.is_staff and cert.user != request.user:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        format_type = request.query_params.get('format', 'pem')
        
        if format_type == 'pem':
            response = HttpResponse(
                cert.certificate_pem,
                content_type='application/x-pem-file'
            )
            response['Content-Disposition'] = f'attachment; filename="certificate_{cert.serial_number}.pem"'
        elif format_type == 'der':
            from cryptography.hazmat.primitives.serialization import Encoding
            from cryptography import x509
            x509_cert = x509.load_pem_x509_certificate(cert.certificate_pem.encode())
            der_data = x509_cert.public_bytes(Encoding.DER)
            response = HttpResponse(
                der_data,
                content_type='application/x-x509-user-cert'
            )
            response['Content-Disposition'] = f'attachment; filename="certificate_{cert.serial_number}.der"'
        else:
            return Response(
                {'error': 'Invalid format. Use pem or der.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        log_pki_action(
            request, 'DOWNLOAD_CERTIFICATE', 'UserCertificate', cert.id,
            {'format': format_type}
        )
        
        return response
    
    @action(detail=True, methods=['get'])
    def chain(self, request, pk=None):
        """Get certificate chain."""
        cert = self.get_object()
        chain = [cert.certificate_pem]
        
        ca = cert.issuing_ca
        while ca:
            chain.append(ca.certificate_pem)
            ca = ca.parent
        
        return Response({
            'chain': chain,
            'chain_pem': '\n'.join(chain)
        })


# ============ Certificate Request Views ============

class CertificateRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Certificate Requests.
    
    Users can create and view their own requests.
    Admins/Officers can approve/reject requests.
    """
    serializer_class = CertificateRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter requests based on user role."""
        user = self.request.user
        queryset = CertificateRequest.objects.select_related(
            'user', 'approved_by', 'issued_certificate'
        )
        
        if user.is_staff or getattr(user, 'is_officer', False):
            # Filter by status if specified
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter.upper())
        else:
            queryset = queryset.filter(user=user)
        
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create a new certificate request."""
        serializer = CertificateRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        cert_service = CertificateService()
        
        try:
            cert_request = cert_service.create_certificate_request(
                user=request.user,
                certificate_type=data['certificate_type'],
                common_name=data.get('common_name', request.user.get_full_name() or request.user.email),
                email=request.user.email,
                organization=data.get('organization', ''),
                organizational_unit=data.get('organizational_unit', ''),
                country=data.get('country', 'VN'),
                state=data.get('state', ''),
                locality=data.get('locality', ''),
                key_algorithm=data.get('key_algorithm', 'RSA-4096'),
                pq_algorithm=data.get('pq_algorithm', 'DILITHIUM3'),
            )
            
            log_pki_action(
                request, 'CREATE_REQUEST', 'CertificateRequest', cert_request.id,
                {'type': data['certificate_type']}
            )
            
            return Response(
                CertificateRequestSerializer(cert_request).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrOfficer])
    def approve(self, request, pk=None):
        """Approve a certificate request."""
        cert_request = self.get_object()
        
        serializer = CertificateApprovalSerializer(data={
            'request_id': cert_request.id,
            **request.data
        })
        serializer.is_valid(raise_exception=True)
        
        ca_id = serializer.validated_data['ca_id']
        ca = get_object_or_404(CertificateAuthority, id=ca_id, is_active=True)
        
        cert_service = CertificateService()
        
        try:
            with transaction.atomic():
                certificate = cert_service.approve_request(
                    cert_request,
                    ca=ca,
                    approved_by=request.user,
                    validity_days=serializer.validated_data.get('validity_days', 365)
                )
                
                log_pki_action(
                    request, 'APPROVE_REQUEST', 'CertificateRequest', cert_request.id,
                    {
                        'certificate_id': certificate.id,
                        'ca_id': ca.id,
                    }
                )
                
                return Response({
                    'status': 'Request approved.',
                    'certificate': UserCertificateSerializer(certificate).data
                })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrOfficer])
    def reject(self, request, pk=None):
        """Reject a certificate request."""
        cert_request = self.get_object()
        
        serializer = CertificateRejectionSerializer(data={
            'request_id': cert_request.id,
            **request.data
        })
        serializer.is_valid(raise_exception=True)
        
        cert_request.status = 'REJECTED'
        cert_request.rejection_reason = serializer.validated_data['reason']
        cert_request.save()
        
        log_pki_action(
            request, 'REJECT_REQUEST', 'CertificateRequest', cert_request.id,
            {'reason': serializer.validated_data['reason']}
        )
        
        return Response({'status': 'Request rejected.'})


# ============ CRL Views ============

class CRLViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CRL management (read-only for most users)."""
    
    queryset = CRL.objects.select_related('issuing_ca').order_by('-created_at')
    serializer_class = CRLSerializer
    permission_classes = [permissions.AllowAny]  # CRLs are public
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download CRL in PEM or DER format."""
        crl = self.get_object()
        format_type = request.query_params.get('format', 'pem')
        
        if format_type == 'pem':
            response = HttpResponse(
                crl.crl_pem,
                content_type='application/x-pem-file'
            )
            response['Content-Disposition'] = f'attachment; filename="crl_{crl.crl_number}.pem"'
        elif format_type == 'der':
            from cryptography.hazmat.primitives.serialization import Encoding
            from cryptography import x509
            x509_crl = x509.load_pem_x509_crl(crl.crl_pem.encode())
            der_data = x509_crl.public_bytes(Encoding.DER)
            response = HttpResponse(
                der_data,
                content_type='application/pkix-crl'
            )
            response['Content-Disposition'] = f'attachment; filename="crl_{crl.crl_number}.crl"'
        else:
            return Response(
                {'error': 'Invalid format.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return response


# ============ Authentication Views ============

class CertificateAuthView(APIView):
    """
    Certificate-based authentication endpoints.
    
    Supports:
    1. TLS client certificate (extracted by middleware)
    2. Challenge-response authentication
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """
        Check if user is authenticated via client certificate.
        
        Returns user info if authenticated, or challenge info if not.
        """
        if hasattr(request, 'client_cert') and request.client_cert.get('verified'):
            # Try to authenticate using the certificate
            from .auth.backends import CertificateAuthenticationBackend
            backend = CertificateAuthenticationBackend()
            user = backend.authenticate(request, certificate_pem=request.client_cert['certificate_pem'])
            
            if user:
                return Response({
                    'authenticated': True,
                    'method': 'client_certificate',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'name': user.get_full_name(),
                    }
                })
        
        return Response({
            'authenticated': False,
            'message': 'No valid client certificate provided.',
            'challenge_url': '/api/pki/auth/challenge/'
        })


class ChallengeAuthView(APIView):
    """
    Challenge-response authentication.
    
    1. Client requests a challenge
    2. Server returns a random challenge
    3. Client signs the challenge with their private key
    4. Server verifies and authenticates
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Request a new authentication challenge."""
        serializer = ChallengeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        fingerprint = serializer.validated_data['certificate_fingerprint']
        
        # Find the certificate
        try:
            certificate = UserCertificate.objects.get(
                user__email=email,
                fingerprint=fingerprint,
                revocation_date__isnull=True,
            )
            
            # Check validity
            now = timezone.now()
            if certificate.valid_from > now or certificate.valid_until < now:
                return Response(
                    {'error': 'Certificate has expired or is not yet valid.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except UserCertificate.DoesNotExist:
            return Response(
                {'error': 'Certificate not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate challenge
        backend = ChallengeResponseAuthBackend()
        challenge = backend.generate_challenge(certificate)
        
        return Response({
            'challenge_id': challenge['challenge_id'],
            'challenge': challenge['challenge_b64'],
            'algorithm': certificate.key_algorithm,
            'pq_algorithm': certificate.pq_algorithm,
            'expires_in': 300,  # 5 minutes
        })


class ChallengeVerifyView(APIView):
    """Verify challenge response and authenticate."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Verify the signed challenge."""
        serializer = ChallengeResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        backend = ChallengeResponseAuthBackend()
        user = backend.authenticate(
            request,
            challenge_id=serializer.validated_data['challenge_id'],
            classical_signature=serializer.validated_data['classical_signature'],
            pq_signature=serializer.validated_data.get('pq_signature'),
        )
        
        if user:
            # Generate tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            log_pki_action(
                request, 'CERTIFICATE_LOGIN', 'User', user.id,
                {'method': 'challenge_response'}
            )
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.get_full_name(),
                }
            })
        
        return Response(
            {'error': 'Authentication failed. Invalid signature.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


# ============ PDF Signing Views ============

class PDFSignView(APIView):
    """
    PDF signing endpoint.
    
    Signs a PDF document with the user's certificate.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Sign an uploaded PDF."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No PDF file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pdf_file = request.FILES['file']
        
        # Get certificate
        cert_id = request.data.get('certificate_id')
        if not cert_id:
            # Use user's default certificate
            certificate = UserCertificate.objects.filter(
                user=request.user,
                revocation_date__isnull=True,
                valid_until__gte=timezone.now(),
            ).first()
            
            if not certificate:
                return Response(
                    {'error': 'No valid certificate found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            try:
                certificate = UserCertificate.objects.get(
                    id=cert_id,
                    user=request.user,
                    revocation_date__isnull=True,
                )
            except UserCertificate.DoesNotExist:
                return Response(
                    {'error': 'Certificate not found or not owned by user.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Check certificate validity
        if not certificate.is_valid:
            return Response(
                {'error': 'Certificate is not valid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save PDF to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_in:
            for chunk in pdf_file.chunks():
                tmp_in.write(chunk)
            tmp_in_path = tmp_in.name
        
        try:
            # Sign the PDF
            pdf_service = PDFSigningService()
            output_path = tmp_in_path.replace('.pdf', '_signed.pdf')
            
            result = pdf_service.sign_pdf(
                pdf_path=tmp_in_path,
                output_path=output_path,
                certificate=certificate,
                reason=request.data.get('reason', 'Digital Signature'),
                location=request.data.get('location', ''),
                contact=request.data.get('contact', request.user.email),
            )
            
            if not result['success']:
                return Response(
                    {'error': result.get('error', 'Failed to sign PDF.')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Log the action
            log_pki_action(
                request, 'SIGN_PDF', 'PDF', None,
                {
                    'certificate_id': certificate.id,
                    'filename': pdf_file.name,
                }
            )
            
            # Return signed PDF
            with open(output_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="signed_{pdf_file.name}"'
                return response
        
        finally:
            # Cleanup temp files
            if os.path.exists(tmp_in_path):
                os.unlink(tmp_in_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class PDFVerifyView(APIView):
    """
    PDF signature verification endpoint.
    
    Verifies digital signatures on a PDF document.
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        """Verify signatures on an uploaded PDF."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No PDF file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pdf_file = request.FILES['file']
        
        # Save PDF to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            for chunk in pdf_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        
        try:
            pdf_service = PDFSigningService()
            result = pdf_service.verify_pdf_signature(tmp_path)
            
            return Response(result)
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


# ============ Audit Log Views ============

class PKIAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs (admin only)."""
    
    queryset = PKIAuditLog.objects.select_related('actor').order_by('-timestamp')
    serializer_class = PKIAuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter audit logs."""
        queryset = super().get_queryset()
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by resource type
        resource_type = self.request.query_params.get('resource_type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)
        
        # Filter by success
        success = self.request.query_params.get('success')
        if success is not None:
            queryset = queryset.filter(success=(success.lower() == 'true'))
        
        return queryset


# ============ Status/Info Views ============

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def pki_status(request):
    """Get PKI system status."""
    return Response({
        'status': 'operational',
        'version': '1.0.0',
        'features': {
            'classical_crypto': True,
            'post_quantum': True,
            'hybrid_signatures': True,
            'pdf_signing': True,
            'certificate_auth': True,
        },
        'algorithms': {
            'classical': ['RSA-2048', 'RSA-4096', 'ECDSA-P256', 'ECDSA-P384'],
            'post_quantum': ['DILITHIUM2', 'DILITHIUM3', 'DILITHIUM5', 'FALCON-512'],
        },
        'ca_count': CertificateAuthority.objects.filter(is_active=True).count(),
        'certificate_count': UserCertificate.objects.filter(
            revocation_date__isnull=True
        ).count(),
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_certificates(request):
    """Get current user's certificates."""
    certificates = UserCertificate.objects.filter(
        user=request.user
    ).select_related('issuing_ca')
    
    return Response({
        'certificates': UserCertificateSerializer(certificates, many=True).data,
        'valid_count': sum(1 for c in certificates if c.is_valid),
        'revoked_count': sum(1 for c in certificates if c.is_revoked),
    })
