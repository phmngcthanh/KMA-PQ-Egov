# Code Analysis: PKI Views & API Module
## E-Government PKI System - NT208

**Module:** `backend/pki/views.py`, `backend/pki/urls.py`  
**Version:** 1.0  
**Date:** December 4, 2025

---

## Overview

The views module provides REST API endpoints for PKI operations using Django REST Framework ViewSets and APIViews.

### URL Structure

```
/api/pki/
├── ca/                          # Certificate Authority management
├── certificates/                # User certificates
├── requests/                    # Certificate requests
├── crl/                         # Certificate Revocation Lists
├── audit/                       # Audit logs
├── auth/                        # Certificate authentication
├── pdf/                         # PDF signing operations
├── status/                      # System status
└── my-certificates/             # User's certificates
```

---

## 1. Permission Classes

### Class: `IsAdminOrOfficer`

```python
class IsAdminOrOfficer(permissions.BasePermission):
    """Permission for admin or officer users."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_staff or getattr(request.user, 'is_officer', False)
```

**Usage:** Certificate request approval, certificate revocation

---

### Class: `IsCertificateOwner`

```python
class IsCertificateOwner(permissions.BasePermission):
    """Permission for certificate owner."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user
```

**Usage:** Certificate download, certificate details

---

## 2. Helper Functions

### Function: `log_pki_action`

```python
def log_pki_action(request, action, resource_type, resource_id, 
                   details=None, success=True, error_message=None):
    """Create an audit log entry."""
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `request` | Request | HTTP request |
| `action` | str | Action type (CREATE_CA, SIGN_PDF, etc.) |
| `resource_type` | str | Resource type (CertificateAuthority, etc.) |
| `resource_id` | str | Resource identifier |
| `details` | dict | Additional details |
| `success` | bool | Operation success |
| `error_message` | str | Error description |

---

### Function: `get_client_ip`

```python
def get_client_ip(request) -> str:
    """Get client IP address from request."""
```

**Returns:** Client IP address (handles X-Forwarded-For header)

---

## 3. Certificate Authority ViewSet

### Class: `CertificateAuthorityViewSet`

```python
class CertificateAuthorityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Certificate Authority management.
    
    Only admin users can manage CAs.
    """
    queryset = CertificateAuthority.objects.all()
    serializer_class = CertificateAuthoritySerializer
    permission_classes = [permissions.IsAdminUser]
```

#### Endpoints

| Method | URL | Action | Description |
|--------|-----|--------|-------------|
| GET | `/api/pki/ca/` | list | List all CAs |
| POST | `/api/pki/ca/` | create | Create new CA |
| GET | `/api/pki/ca/{id}/` | retrieve | Get CA details |
| PUT | `/api/pki/ca/{id}/` | update | Update CA |
| DELETE | `/api/pki/ca/{id}/` | destroy | Delete CA |
| POST | `/api/pki/ca/{id}/generate_crl/` | generate_crl | Generate CRL |
| GET | `/api/pki/ca/{id}/download_certificate/` | download_certificate | Download CA cert |
| GET | `/api/pki/ca/{id}/chain/` | chain | Get CA chain |

---

#### Method: `get_queryset`

```python
def get_queryset(self):
    """Filter CAs by type if specified."""
    queryset = super().get_queryset()
    ca_type = self.request.query_params.get('type')
    if ca_type:
        queryset = queryset.filter(ca_type=ca_type.upper())
    return queryset.select_related('parent')
```

**Query Parameters:**
- `type`: Filter by CA type (ROOT, INTERMEDIATE_OFFICER, etc.)

---

#### Method: `create`

```python
def create(self, request, *args, **kwargs):
    """Create a new Certificate Authority."""
```

**Request Body (Root CA):**
```json
{
    "name": "E-Gov Root CA",
    "ca_type": "ROOT",
    "organization": "Ministry of Information",
    "country": "VN",
    "key_algorithm": "RSA-4096",
    "pq_algorithm": "DILITHIUM3",
    "validity_days": 7300
}
```

**Request Body (Intermediate CA):**
```json
{
    "name": "Officer Issuing CA",
    "ca_type": "INTERMEDIATE_OFFICER",
    "parent_id": 1,
    "organization": "Ministry of Information",
    "country": "VN"
}
```

**Response:** `201 Created`
```json
{
    "id": 1,
    "name": "E-Gov Root CA",
    "ca_type": "ROOT",
    "is_active": true,
    "certificate_pem": "-----BEGIN CERTIFICATE-----...",
    "serial_number": "ABC123...",
    "valid_from": "2025-12-04T10:00:00Z",
    "valid_until": "2045-12-04T10:00:00Z"
}
```

---

#### Action: `generate_crl`

```python
@action(detail=True, methods=['post'])
def generate_crl(self, request, pk=None):
    """Generate a new CRL for this CA."""
```

**Response:**
```json
{
    "id": 1,
    "crl_number": 5,
    "entries_count": 12,
    "this_update": "2025-12-04T10:00:00Z",
    "next_update": "2025-12-11T10:00:00Z"
}
```

---

#### Action: `download_certificate`

```python
@action(detail=True, methods=['get'])
def download_certificate(self, request, pk=None):
    """Download CA certificate."""
```

**Query Parameters:**
- `format`: `pem` (default) or `der`

**Response:** File download with appropriate content type

---

#### Action: `chain`

```python
@action(detail=True, methods=['get'])
def chain(self, request, pk=None):
    """Get certificate chain for this CA."""
```

**Response:**
```json
{
    "chain": [
        {
            "id": 2,
            "name": "Officer CA",
            "type": "INTERMEDIATE_OFFICER",
            "certificate_pem": "..."
        },
        {
            "id": 1,
            "name": "Root CA",
            "type": "ROOT",
            "certificate_pem": "..."
        }
    ]
}
```

---

## 4. User Certificate ViewSet

### Class: `UserCertificateViewSet`

```python
class UserCertificateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User Certificates.
    
    Users can view their own certificates.
    Admins/Officers can view all certificates.
    """
    serializer_class = UserCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
```

#### Endpoints

| Method | URL | Action | Description |
|--------|-----|--------|-------------|
| GET | `/api/pki/certificates/` | list | List certificates |
| GET | `/api/pki/certificates/{id}/` | retrieve | Get certificate |
| POST | `/api/pki/certificates/{id}/revoke/` | revoke | Revoke certificate |
| GET | `/api/pki/certificates/{id}/download/` | download | Download certificate |
| GET | `/api/pki/certificates/{id}/chain/` | chain | Get cert chain |

---

#### Method: `get_queryset`

```python
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
```

**Query Parameters:**
- `valid_only`: Filter to only valid certificates

---

#### Action: `revoke`

```python
@action(detail=True, methods=['post'])
def revoke(self, request, pk=None):
    """Revoke a certificate."""
```

**Permission:** `IsAdminOrOfficer`

**Request Body:**
```json
{
    "reason": "KEY_COMPROMISE"
}
```

**Response:**
```json
{
    "status": "Certificate revoked successfully."
}
```

---

#### Action: `download`

```python
@action(detail=True, methods=['get'])
def download(self, request, pk=None):
    """Download certificate in various formats."""
```

**Query Parameters:**
- `format`: `pem` (default) or `der`

**Security:** Checks certificate ownership

---

#### Action: `chain`

```python
@action(detail=True, methods=['get'])
def chain(self, request, pk=None):
    """Get certificate chain."""
```

**Response:**
```json
{
    "chain": ["<user-cert-pem>", "<intermediate-ca-pem>", "<root-ca-pem>"],
    "chain_pem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n..."
}
```

---

## 5. Certificate Request ViewSet

### Class: `CertificateRequestViewSet`

```python
class CertificateRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Certificate Requests.
    
    Users can create and view their own requests.
    Admins/Officers can approve/reject requests.
    """
    serializer_class = CertificateRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
```

#### Endpoints

| Method | URL | Action | Description |
|--------|-----|--------|-------------|
| GET | `/api/pki/requests/` | list | List requests |
| POST | `/api/pki/requests/` | create | Create request |
| GET | `/api/pki/requests/{id}/` | retrieve | Get request |
| POST | `/api/pki/requests/{id}/approve/` | approve | Approve request |
| POST | `/api/pki/requests/{id}/reject/` | reject | Reject request |

---

#### Method: `create`

```python
def create(self, request, *args, **kwargs):
    """Create a new certificate request."""
```

**Request Body:**
```json
{
    "certificate_type": "CITIZEN",
    "common_name": "Nguyen Van A",
    "organization": "",
    "organizational_unit": "",
    "country": "VN",
    "state": "Ho Chi Minh",
    "locality": "District 1",
    "key_algorithm": "RSA-4096",
    "pq_algorithm": "DILITHIUM3"
}
```

**Response:** `201 Created`
```json
{
    "id": "uuid",
    "status": "PENDING",
    "certificate_type": "CITIZEN",
    "common_name": "Nguyen Van A",
    "created_at": "2025-12-04T10:00:00Z"
}
```

---

#### Action: `approve`

```python
@action(detail=True, methods=['post'], permission_classes=[IsAdminOrOfficer])
def approve(self, request, pk=None):
    """Approve a certificate request."""
```

**Request Body:**
```json
{
    "ca_id": 2,
    "validity_days": 365
}
```

**Response:**
```json
{
    "status": "Request approved.",
    "certificate": {
        "id": "uuid",
        "serial_number": "ABC123...",
        "valid_from": "2025-12-04T10:00:00Z",
        "valid_until": "2026-12-04T10:00:00Z"
    }
}
```

---

#### Action: `reject`

```python
@action(detail=True, methods=['post'], permission_classes=[IsAdminOrOfficer])
def reject(self, request, pk=None):
    """Reject a certificate request."""
```

**Request Body:**
```json
{
    "reason": "Incomplete identity verification"
}
```

**Response:**
```json
{
    "status": "Request rejected."
}
```

---

## 6. CRL ViewSet

### Class: `CRLViewSet`

```python
class CRLViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for CRL management (read-only for most users)."""
    
    queryset = CRL.objects.select_related('issuing_ca').order_by('-created_at')
    serializer_class = CRLSerializer
    permission_classes = [permissions.AllowAny]  # CRLs are public
```

#### Endpoints

| Method | URL | Action | Description |
|--------|-----|--------|-------------|
| GET | `/api/pki/crl/` | list | List CRLs |
| GET | `/api/pki/crl/{id}/` | retrieve | Get CRL details |
| GET | `/api/pki/crl/{id}/download/` | download | Download CRL |

---

#### Action: `download`

```python
@action(detail=True, methods=['get'])
def download(self, request, pk=None):
    """Download CRL in PEM or DER format."""
```

**Query Parameters:**
- `format`: `pem` (default) or `der`

**Response:** File download
- PEM: `application/x-pem-file`
- DER: `application/pkix-crl`

---

## 7. Certificate Authentication Views

### Class: `CertificateAuthView`

```python
class CertificateAuthView(APIView):
    """
    Certificate-based authentication endpoints.
    
    Supports:
    1. TLS client certificate (extracted by middleware)
    2. Challenge-response authentication
    """
    permission_classes = [permissions.AllowAny]
```

#### Method: `get`

**URL:** `GET /api/pki/auth/`

**Purpose:** Check if user is authenticated via client certificate

**Response (Authenticated):**
```json
{
    "authenticated": true,
    "method": "client_certificate",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "name": "Nguyen Van A"
    }
}
```

**Response (Not Authenticated):**
```json
{
    "authenticated": false,
    "message": "No valid client certificate provided.",
    "challenge_url": "/api/pki/auth/challenge/"
}
```

---

### Class: `ChallengeAuthView`

```python
class ChallengeAuthView(APIView):
    """
    Challenge-response authentication.
    
    1. Client requests a challenge
    2. Server returns a random challenge
    3. Client signs the challenge with their private key
    4. Server verifies and authenticates
    """
    permission_classes = [permissions.AllowAny]
```

#### Method: `post`

**URL:** `POST /api/pki/auth/challenge/`

**Request Body:**
```json
{
    "email": "user@example.com",
    "certificate_fingerprint": "ABC123..."
}
```

**Response:**
```json
{
    "challenge_id": "uuid",
    "challenge": "<base64-encoded-random-bytes>",
    "algorithm": "RSA_4096",
    "pq_algorithm": "DILITHIUM3",
    "expires_in": 300
}
```

---

### Class: `ChallengeVerifyView`

```python
class ChallengeVerifyView(APIView):
    """Verify challenge response and authenticate."""
    permission_classes = [permissions.AllowAny]
```

#### Method: `post`

**URL:** `POST /api/pki/auth/verify/`

**Request Body:**
```json
{
    "challenge_id": "uuid",
    "classical_signature": "<base64-rsa-signature>",
    "pq_signature": "<base64-dilithium-signature>"
}
```

**Response (Success):**
```json
{
    "access": "<jwt-access-token>",
    "refresh": "<jwt-refresh-token>",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "name": "Nguyen Van A"
    }
}
```

**Response (Failure):**
```json
{
    "error": "Authentication failed. Invalid signature."
}
```

---

## 8. PDF Signing Views

### Class: `PDFSignView`

```python
class PDFSignView(APIView):
    """
    PDF signing endpoint.
    
    Signs a PDF document with the user's certificate.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
```

#### Method: `post`

**URL:** `POST /api/pki/pdf/sign/`

**Request:** `multipart/form-data`
- `file`: PDF file
- `certificate_id`: Certificate ID (optional, uses default)
- `reason`: Signing reason
- `location`: Signing location

**Response:** Signed PDF file download

**cURL Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "reason=Phê duyệt hồ sơ" \
  -F "location=TP. Hồ Chí Minh" \
  https://api.example.com/api/pki/pdf/sign/ \
  --output signed_document.pdf
```

---

### Class: `PDFVerifyView`

```python
class PDFVerifyView(APIView):
    """
    PDF signature verification endpoint.
    
    Verifies digital signatures on a PDF document.
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
```

#### Method: `post`

**URL:** `POST /api/pki/pdf/verify/`

**Request:** `multipart/form-data`
- `file`: PDF file to verify

**Response:**
```json
{
    "valid": true,
    "classical_valid": true,
    "pq_valid": true,
    "certificate_valid": true,
    "signer": "CN=Nguyen Van A, O=...",
    "signed_at": "2025-12-04T10:00:00Z",
    "errors": [],
    "warnings": []
}
```

---

## 9. Audit Log ViewSet

### Class: `PKIAuditLogViewSet`

```python
class PKIAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs (admin only)."""
    
    queryset = PKIAuditLog.objects.select_related('actor').order_by('-timestamp')
    serializer_class = PKIAuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
```

#### Endpoints

| Method | URL | Action | Description |
|--------|-----|--------|-------------|
| GET | `/api/pki/audit/` | list | List audit logs |
| GET | `/api/pki/audit/{id}/` | retrieve | Get log details |

#### Query Parameters

- `action`: Filter by action type
- `resource_type`: Filter by resource type
- `date_from`: Filter from date
- `date_to`: Filter to date
- `success`: Filter by success status

---

## 10. Status & Info Endpoints

### Function: `pki_status`

```python
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def pki_status(request):
    """Get PKI system status."""
```

**URL:** `GET /api/pki/status/`

**Response:**
```json
{
    "status": "operational",
    "version": "1.0.0",
    "features": {
        "classical_crypto": true,
        "post_quantum": true,
        "hybrid_signatures": true,
        "pdf_signing": true,
        "certificate_auth": true
    },
    "algorithms": {
        "classical": ["RSA-2048", "RSA-4096", "ECDSA-P256", "ECDSA-P384"],
        "post_quantum": ["DILITHIUM2", "DILITHIUM3", "DILITHIUM5", "FALCON-512"]
    },
    "ca_count": 3,
    "certificate_count": 150
}
```

---

### Function: `my_certificates`

```python
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_certificates(request):
    """Get current user's certificates."""
```

**URL:** `GET /api/pki/my-certificates/`

**Response:**
```json
{
    "certificates": [
        {
            "id": "uuid",
            "serial_number": "ABC123...",
            "certificate_type": "CITIZEN",
            "key_algorithm": "RSA_4096",
            "pq_algorithm": "DILITHIUM3",
            "valid_until": "2026-12-04T10:00:00Z",
            "is_valid": true
        }
    ],
    "valid_count": 1,
    "revoked_count": 0
}
```

---

## 11. URL Configuration

```python
# backend/pki/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ca', views.CertificateAuthorityViewSet, basename='ca')
router.register(r'certificates', views.UserCertificateViewSet, basename='certificate')
router.register(r'requests', views.CertificateRequestViewSet, basename='certificate-request')
router.register(r'crl', views.CRLViewSet, basename='crl')
router.register(r'audit', views.PKIAuditLogViewSet, basename='audit')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Status/Info
    path('status/', views.pki_status, name='pki-status'),
    path('my-certificates/', views.my_certificates, name='my-certificates'),
    
    # Authentication
    path('auth/', views.CertificateAuthView.as_view(), name='cert-auth'),
    path('auth/challenge/', views.ChallengeAuthView.as_view(), name='challenge-auth'),
    path('auth/verify/', views.ChallengeVerifyView.as_view(), name='challenge-verify'),
    
    # PDF Operations
    path('pdf/sign/', views.PDFSignView.as_view(), name='pdf-sign'),
    path('pdf/verify/', views.PDFVerifyView.as_view(), name='pdf-verify'),
]
```

---

## 12. Error Responses

### Standard Error Format

```json
{
    "error": "Error message here"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

### Validation Errors

```json
{
    "field_name": [
        "Error message 1",
        "Error message 2"
    ]
}
```
