# Code Analysis: Document Submission Module (Hồ Sơ)
## E-Government PKI System - NT208

**Module:** `backend/hoso/`  
**Version:** 1.0  
**Date:** December 4, 2025

---

## Overview

The `hoso` (document/application) module manages the citizen document submission system for the e-government platform. It handles administrative procedures, document submissions, officer processing, and status tracking.

### Module Structure

```
backend/hoso/
├── __init__.py
├── admin.py           # Django admin configuration
├── apps.py            # App configuration
├── models.py          # Data models
├── serializers.py     # DRF serializers
├── urls.py            # URL routing
├── views.py           # API views
├── paginator.py       # Custom pagination
├── utils.py           # Utility functions
├── signpdf.py         # PDF signing
└── static/image/      # Static assets
```

---

## 1. Data Models (`hoso/models.py`)

### Class: `HoSo`

```python
class HoSo(models.Model):
    """
    Administrative procedure template.
    
    Defines types of government services/procedures available.
    """
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `loaihoso` | CharField(255) | Procedure type |
| `tieude` | CharField(255) | Title |
| `noidung` | TextField | Content/instructions |
| `image` | ImageField | Associated image |
| `ngaydang` | DateTimeField | Publication date (auto) |
| `ngaycapnhat` | DateTimeField | Last update (auto) |

---

### Class: `CauHoi`

```python
class CauHoi(models.Model):
    """
    User questions/inquiries about procedures.
    """
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `hoso` | ForeignKey(HoSo) | Related procedure |
| `nguoitao` | ForeignKey(User) | Question author |
| `noidung` | TextField | Question content |
| `ngaydang` | DateTimeField | Posted date (auto) |
| `cauhoipublic` | BooleanField | Public visibility |

---

### Class: `TraLoiCauHoi`

```python
class TraLoiCauHoi(models.Model):
    """
    Answers to user questions.
    """
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `cauhoi` | ForeignKey(CauHoi) | Related question |
| `nguoitao` | ForeignKey(User) | Answer author |
| `noidung` | TextField | Answer content |
| `ngaydang` | DateTimeField | Posted date (auto) |

---

### Class: `NopHoSo`

```python
class NopHoSo(models.Model):
    """
    Document submission by citizen.
    
    Represents a citizen's application for a government service.
    """
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `hoso` | ForeignKey(HoSo) | Procedure type |
| `nguoitao` | ForeignKey(User) | Submitter |
| `noidung` | TextField | Content/details |
| `image` | ImageField | Attached document/image |
| `ngaydang` | DateTimeField | Submission date |
| `hosoduocky` | FileField | Signed document |
| `status` | IntegerField | Status (0: pending, 1: approved, 2: rejected) |

#### Status Values

```python
STATUS_CHOICES = [
    (0, 'Pending'),      # Chờ xử lý
    (1, 'Approved'),     # Đã duyệt
    (2, 'Rejected'),     # Từ chối
]
```

---

## 2. Serializers (`hoso/serializers.py`)

### Class: `HoSoSerializer`

```python
class HoSoSerializer(serializers.ModelSerializer):
    """Serializer for procedure templates."""
    
    class Meta:
        model = HoSo
        fields = ['id', 'loaihoso', 'tieude', 'noidung', 'image', 
                  'ngaydang', 'ngaycapnhat']
```

---

### Class: `CauHoiSerializer`

```python
class CauHoiSerializer(serializers.ModelSerializer):
    """Serializer for questions."""
    
    class Meta:
        model = CauHoi
        fields = ['id', 'hoso', 'nguoitao', 'noidung', 'ngaydang', 'cauhoipublic']
```

---

### Class: `TraLoiCauHoiSerializer`

```python
class TraLoiCauHoiSerializer(serializers.ModelSerializer):
    """Serializer for answers."""
    
    class Meta:
        model = TraLoiCauHoi
        fields = ['id', 'cauhoi', 'nguoitao', 'noidung', 'ngaydang']
```

---

### Class: `NopHoSoSerializer`

```python
class NopHoSoSerializer(serializers.ModelSerializer):
    """Serializer for document submissions."""
    
    class Meta:
        model = NopHoSo
        fields = ['id', 'hoso', 'nguoitao', 'noidung', 'image', 
                  'ngaydang', 'hosoduocky', 'status']
```

---

## 3. Views (`hoso/views.py`)

### Class: `HoSoViewSet`

```python
class HoSoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for administrative procedures.
    
    Provides CRUD operations for procedure templates.
    """
    
    queryset = HoSo.objects.all()
    serializer_class = HoSoSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = HoSoPaginator
```

#### Endpoints

| Method | URL | Action | Permission |
|--------|-----|--------|------------|
| GET | `/api/hoso/hoso/` | List all procedures | Public |
| POST | `/api/hoso/hoso/` | Create procedure | Admin only |
| GET | `/api/hoso/hoso/{id}/` | Get procedure | Public |
| PUT | `/api/hoso/hoso/{id}/` | Update procedure | Admin only |
| DELETE | `/api/hoso/hoso/{id}/` | Delete procedure | Admin only |

#### Custom Actions

##### `loai_hoso`

```python
@action(detail=False, methods=['get'])
def loai_hoso(self, request):
    """Get all unique procedure types."""
    loaihoso = HoSo.objects.values_list('loaihoso', flat=True).distinct()
    return Response(loaihoso)
```

**URL:** `GET /api/hoso/hoso/loai_hoso/`

---

### Class: `CauHoiViewSet`

```python
class CauHoiViewSet(viewsets.ModelViewSet):
    """
    ViewSet for questions.
    
    Allows citizens to ask questions about procedures.
    """
    
    queryset = CauHoi.objects.all()
    serializer_class = CauHoiSerializer
    permission_classes = [IsAuthenticated]
```

#### Endpoints

| Method | URL | Action | Permission |
|--------|-----|--------|------------|
| GET | `/api/hoso/cauhoi/` | List questions | Authenticated |
| POST | `/api/hoso/cauhoi/` | Create question | Authenticated |
| GET | `/api/hoso/cauhoi/{id}/` | Get question | Authenticated |
| PUT | `/api/hoso/cauhoi/{id}/` | Update question | Owner |
| DELETE | `/api/hoso/cauhoi/{id}/` | Delete question | Owner/Admin |

#### Custom Actions

##### `get_cauhoi_by_hoso`

```python
@action(detail=False, methods=['get'])
def get_cauhoi_by_hoso(self, request):
    """Get all questions for a specific procedure."""
    hoso_id = request.query_params.get('hoso_id')
    cauhoi = CauHoi.objects.filter(hoso_id=hoso_id, cauhoipublic=True)
    serializer = self.get_serializer(cauhoi, many=True)
    return Response(serializer.data)
```

**URL:** `GET /api/hoso/cauhoi/get_cauhoi_by_hoso/?hoso_id={id}`

---

### Class: `TraLoiCauHoiViewSet`

```python
class TraLoiCauHoiViewSet(viewsets.ModelViewSet):
    """
    ViewSet for answers.
    
    Allows officers to answer citizen questions.
    """
    
    queryset = TraLoiCauHoi.objects.all()
    serializer_class = TraLoiCauHoiSerializer
    permission_classes = [IsOfficerOrReadOnly]
```

#### Endpoints

| Method | URL | Action | Permission |
|--------|-----|--------|------------|
| GET | `/api/hoso/traloi/` | List answers | Public |
| POST | `/api/hoso/traloi/` | Create answer | Officer only |
| GET | `/api/hoso/traloi/{id}/` | Get answer | Public |
| PUT | `/api/hoso/traloi/{id}/` | Update answer | Officer |
| DELETE | `/api/hoso/traloi/{id}/` | Delete answer | Officer/Admin |

#### Custom Actions

##### `get_traloi_by_cauhoi`

```python
@action(detail=False, methods=['get'])
def get_traloi_by_cauhoi(self, request):
    """Get all answers for a specific question."""
    cauhoi_id = request.query_params.get('cauhoi_id')
    traloi = TraLoiCauHoi.objects.filter(cauhoi_id=cauhoi_id)
    serializer = self.get_serializer(traloi, many=True)
    return Response(serializer.data)
```

**URL:** `GET /api/hoso/traloi/get_traloi_by_cauhoi/?cauhoi_id={id}`

---

### Class: `NopHoSoViewSet`

```python
class NopHoSoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for document submissions.
    
    Handles citizen applications and officer processing.
    """
    
    queryset = NopHoSo.objects.all()
    serializer_class = NopHoSoSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
```

#### Endpoints

| Method | URL | Action | Permission |
|--------|-----|--------|------------|
| GET | `/api/hoso/nophoso/` | List submissions | Authenticated |
| POST | `/api/hoso/nophoso/` | Submit document | Authenticated |
| GET | `/api/hoso/nophoso/{id}/` | Get submission | Owner/Officer |
| PUT | `/api/hoso/nophoso/{id}/` | Update submission | Owner/Officer |
| DELETE | `/api/hoso/nophoso/{id}/` | Delete submission | Owner/Admin |

#### Custom Actions

##### `get_my_hoso`

```python
@action(detail=False, methods=['get'])
def get_my_hoso(self, request):
    """Get current user's submissions."""
    hoso = NopHoSo.objects.filter(nguoitao=request.user)
    serializer = self.get_serializer(hoso, many=True)
    return Response(serializer.data)
```

**URL:** `GET /api/hoso/nophoso/get_my_hoso/`

##### `approve`

```python
@action(detail=True, methods=['post'])
def approve(self, request, pk=None):
    """Approve a submission (officer only)."""
    hoso = self.get_object()
    hoso.status = 1  # Approved
    hoso.save()
    return Response({'status': 'approved'})
```

**URL:** `POST /api/hoso/nophoso/{id}/approve/`

##### `reject`

```python
@action(detail=True, methods=['post'])
def reject(self, request, pk=None):
    """Reject a submission (officer only)."""
    hoso = self.get_object()
    hoso.status = 2  # Rejected
    hoso.save()
    return Response({'status': 'rejected'})
```

**URL:** `POST /api/hoso/nophoso/{id}/reject/`

##### `sign`

```python
@action(detail=True, methods=['post'])
def sign(self, request, pk=None):
    """Sign the submission document (officer only)."""
    hoso = self.get_object()
    # Sign the document using PKI
    signed_path = sign_document(hoso.image.path, request.user)
    hoso.hosoduocky = signed_path
    hoso.status = 1
    hoso.save()
    return Response({'status': 'signed', 'path': signed_path})
```

**URL:** `POST /api/hoso/nophoso/{id}/sign/`

##### `get_pending`

```python
@action(detail=False, methods=['get'])
def get_pending(self, request):
    """Get all pending submissions (officer only)."""
    hoso = NopHoSo.objects.filter(status=0)
    serializer = self.get_serializer(hoso, many=True)
    return Response(serializer.data)
```

**URL:** `GET /api/hoso/nophoso/get_pending/`

---

## 4. Custom Pagination (`hoso/paginator.py`)

### Class: `HoSoPaginator`

```python
class HoSoPaginator(PageNumberPagination):
    """Custom pagination for procedure listing."""
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
```

**Usage:**
```
GET /api/hoso/hoso/?page=1&page_size=20
```

---

## 5. URL Configuration

```python
# backend/hoso/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HoSoViewSet, CauHoiViewSet, 
    TraLoiCauHoiViewSet, NopHoSoViewSet
)

router = DefaultRouter()
router.register(r'hoso', HoSoViewSet)
router.register(r'cauhoi', CauHoiViewSet)
router.register(r'traloi', TraLoiCauHoiViewSet)
router.register(r'nophoso', NopHoSoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## 6. Document Signing (`hoso/signpdf.py`)

### Function: `sign_document`

```python
def sign_document(file_path, user):
    """
    Sign a document using the officer's certificate.
    
    Args:
        file_path: Path to the document
        user: Officer user object
        
    Returns:
        Path to signed document
    """
```

**Process:**
1. Get officer's active certificate
2. Load private key
3. Create signature (hybrid if PQ enabled)
4. Embed signature in PDF or create detached signature
5. Save signed document

---

## 7. Workflow Diagrams

### Document Submission Flow

```
┌─────────────┐
│   Citizen   │
└─────────────┘
       │
       │ 1. Submit document
       │    POST /nophoso/
       ▼
┌─────────────────────┐
│    NopHoSo         │
│    status = 0      │
│    (Pending)       │
└─────────────────────┘
       │
       │ 2. Officer reviews
       │    GET /nophoso/get_pending/
       ▼
┌─────────────────────┐
│     Review         │
│     Document       │
└─────────────────────┘
       │
       ├─────────────────────┐
       │                     │
       ▼                     ▼
┌──────────────┐     ┌──────────────┐
│   Approve    │     │   Reject     │
│ POST .../    │     │ POST .../    │
│ approve/     │     │ reject/      │
└──────────────┘     └──────────────┘
       │                     │
       ▼                     ▼
┌──────────────┐     ┌──────────────┐
│  Sign Doc    │     │  status = 2  │
│ POST .../    │     │  (Rejected)  │
│ sign/        │     └──────────────┘
└──────────────┘
       │
       ▼
┌─────────────────────┐
│    status = 1      │
│    (Approved)      │
│    hosoduocky set  │
└─────────────────────┘
       │
       │ 3. Citizen receives
       │    GET /nophoso/get_my_hoso/
       ▼
┌─────────────────────┐
│    Citizen views   │
│    signed document │
└─────────────────────┘
```

### Q&A Flow

```
┌─────────────┐                    ┌─────────────┐
│   Citizen   │                    │   Officer   │
└─────────────┘                    └─────────────┘
       │                                  │
       │ 1. Ask question                  │
       │    POST /cauhoi/                 │
       ▼                                  │
┌─────────────────────┐                   │
│     CauHoi         │                   │
│  cauhoipublic=True │                   │
└─────────────────────┘                   │
       │                                  │
       │ 2. Question visible              │
       │◀─────────────────────────────────┤
       │                                  │
       │                                  │ 3. Answer question
       │                                  │    POST /traloi/
       │                                  ▼
       │                         ┌─────────────────────┐
       │                         │    TraLoiCauHoi     │
       │                         └─────────────────────┘
       │                                  │
       │ 4. View answer                   │
       │    GET /traloi/get_traloi_by_cauhoi/
       ▼                                  │
┌─────────────────────┐                   │
│  Citizen reads     │                   │
│     answer         │                   │
└─────────────────────┘                   │
```

---

## 8. Permissions

### Custom Permission Classes

#### `IsAdminOrReadOnly`

```python
class IsAdminOrReadOnly(BasePermission):
    """
    Allow read access to anyone.
    Allow write access to admin users only.
    """
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
```

#### `IsOfficerOrReadOnly`

```python
class IsOfficerOrReadOnly(BasePermission):
    """
    Allow read access to anyone.
    Allow write access to officers only.
    """
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and (request.user.is_officer or request.user.is_staff)
```

#### `IsOwnerOrOfficer`

```python
class IsOwnerOrOfficer(BasePermission):
    """
    Allow access to owner or officers.
    """
    
    def has_object_permission(self, request, view, obj):
        return (
            obj.nguoitao == request.user or 
            request.user.is_officer or 
            request.user.is_staff
        )
```

---

## 9. API Response Examples

### List Procedures

**Request:**
```http
GET /api/hoso/hoso/
```

**Response:**
```json
{
    "count": 15,
    "next": "http://localhost:8000/api/hoso/hoso/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "loaihoso": "Giấy phép xây dựng",
            "tieude": "Cấp giấy phép xây dựng nhà ở riêng lẻ",
            "noidung": "Hướng dẫn thủ tục cấp giấy phép xây dựng...",
            "image": "/media/hoso/2021/gpxd.png",
            "ngaydang": "2021-12-01T10:00:00Z",
            "ngaycapnhat": "2021-12-03T15:30:00Z"
        }
    ]
}
```

### Submit Document

**Request:**
```http
POST /api/hoso/nophoso/
Content-Type: multipart/form-data

hoso: 1
noidung: Đơn xin cấp giấy phép xây dựng
image: [file]
```

**Response:**
```json
{
    "id": 42,
    "hoso": 1,
    "nguoitao": 5,
    "noidung": "Đơn xin cấp giấy phép xây dựng",
    "image": "/media/hoso/2021/don_xin_42.pdf",
    "ngaydang": "2021-12-04T09:15:00Z",
    "hosoduocky": null,
    "status": 0
}
```

### Approve and Sign

**Request:**
```http
POST /api/hoso/nophoso/42/sign/
Authorization: Bearer <officer-token>
```

**Response:**
```json
{
    "status": "signed",
    "path": "/media/hoso/signed/don_xin_42_signed.pdf"
}
```

---

## 10. Status Tracking

| Status Code | Vietnamese | English | Description |
|-------------|------------|---------|-------------|
| 0 | Chờ xử lý | Pending | Initial state, awaiting officer review |
| 1 | Đã duyệt | Approved | Reviewed and approved by officer |
| 2 | Từ chối | Rejected | Reviewed and rejected by officer |

### Status Transitions

```
     ┌──────────┐
     │  Submit  │
     └──────────┘
          │
          ▼
     ┌──────────┐
     │ Pending  │ (status=0)
     │    0     │
     └──────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
┌───────┐   ┌───────┐
│Approve│   │Reject │
└───────┘   └───────┘
    │           │
    ▼           ▼
┌───────┐   ┌───────┐
│Approved   │Rejected│ (status=2)
│ (1)   │   │  (2)  │
└───────┘   └───────┘
```
