# Code Analysis: Authentication Module
## E-Government PKI System - NT208

**Module:** `backend/authentication/`, `backend/pki/auth/`  
**Version:** 1.0  
**Date:** December 4, 2025

---

## Overview

The authentication module provides user management and multiple authentication methods including username/password, certificate-based, and social authentication.

### Module Structure

```
backend/authentication/
├── __init__.py
├── admin.py           # Django admin configuration
├── apps.py            # App configuration
├── models.py          # User model
├── serializers.py     # DRF serializers
├── urls.py            # URL routing
├── utils.py           # Email utilities
├── views.py           # API views
└── renderers.py       # Custom renderers

backend/pki/auth/
├── __init__.py
├── backends.py        # Certificate auth backends
└── middleware.py      # TLS certificate middleware
```

---

## 1. User Model (`authentication/models.py`)

### Class: `User`

Custom user model extending Django's AbstractBaseUser.

```python
class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email as primary identifier.
    """
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `username` | CharField(255) | Unique username |
| `email` | EmailField(255) | Primary identifier (unique) |
| `is_verified` | BooleanField | Email verified |
| `is_active` | BooleanField | Account active |
| `is_staff` | BooleanField | Staff access |
| `is_officer` | BooleanField | Government officer |
| `created_at` | DateTimeField | Registration time |
| `updated_at` | DateTimeField | Last update |
| `auth_provider` | CharField(255) | Auth method (email, google, facebook) |
| `first_name` | CharField(250) | First name |
| `last_name` | CharField(250) | Last name |
| `phone` | CharField(250) | Phone number |

#### Constants

```python
AUTH_PROVIDERS = {
    'facebook': 'facebook',
    'google': 'google',
    'twitter': 'twitter',
    'email': 'email'
}

USERNAME_FIELD = 'email'
REQUIRED_FIELDS = ['username']
```

#### Methods

##### `tokens()`

```python
def tokens(self):
    """Generate JWT tokens for user."""
    refresh = RefreshToken.for_user(self)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }
```

##### `get_full_name()`

```python
def get_full_name(self):
    """Return user's full name."""
    if self.first_name or self.last_name:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
    return self.username
```

---

### Class: `UserManager`

Custom user manager for User model.

```python
class UserManager(BaseUserManager):
    """Custom manager for User model."""
```

#### Methods

##### `create_user`

```python
def create_user(self, username, email, first_name, last_name, phone, password=None):
    """Create and return a regular user."""
```

**Validations:**
- Username required
- Email required
- First name required
- Last name required
- Phone required

##### `create_superuser`

```python
def create_superuser(self, username, email, password=None, **kwargs):
    """Create and return a superuser."""
```

**Effects:**
- Sets `is_superuser = True`
- Sets `is_staff = True`

---

## 2. Authentication Serializers (`authentication/serializers.py`)

### Class: `RegisterSerializer`

```python
class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'first_name', 'last_name', 'phone']
        extra_kwargs = {'password': {'write_only': True}}
```

**Validation:**
- Email uniqueness
- Username uniqueness
- Password minimum length

---

### Class: `LoginSerializer`

```python
class LoginSerializer(serializers.ModelSerializer):
    """Serializer for user login."""
    
    class Meta:
        model = User
        fields = ['email', 'password', 'tokens']
```

**Process:**
1. Validate email exists
2. Check password
3. Check email verified
4. Return tokens

---

### Class: `EmailVerificationSerializer`

```python
class EmailVerificationSerializer(serializers.ModelSerializer):
    """Serializer for email verification."""
    
    token = serializers.CharField(max_length=555)
```

---

### Class: `ResetPasswordEmailRequestSerializer`

```python
class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    
    email = serializers.EmailField(min_length=2)
    redirect_url = serializers.CharField(max_length=500, required=False)
```

---

### Class: `SetNewPasswordSerializer`

```python
class SetNewPasswordSerializer(serializers.Serializer):
    """Serializer for setting new password."""
    
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)
```

---

### Class: `LogoutSerializer`

```python
class LogoutSerializer(serializers.Serializer):
    """Serializer for logout."""
    
    refresh = serializers.CharField()
```

**Process:**
- Blacklist refresh token

---

## 3. Authentication Views (`authentication/views.py`)

### Class: `RegisterView`

```python
class RegisterView(generics.GenericAPIView):
    """User registration endpoint."""
    
    serializer_class = RegisterSerializer
    renderer_classes = (UserRenderer,)
```

**URL:** `POST /api/auth/register/`

**Request:**
```json
{
    "email": "user@example.com",
    "username": "username",
    "password": "password123",
    "first_name": "Nguyen",
    "last_name": "Van A",
    "phone": "0901234567"
}
```

**Process:**
1. Validate input
2. Create user
3. Generate verification token
4. Send verification email
5. Return user data

**Response:** `201 Created`
```json
{
    "email": "user@example.com",
    "username": "username"
}
```

---

### Class: `VerifyEmail`

```python
class VerifyEmail(views.APIView):
    """Email verification endpoint."""
    
    serializer_class = EmailVerificationSerializer
```

**URL:** `GET /api/auth/email-verify/?token=<token>`

**Process:**
1. Decode JWT token
2. Find user by ID
3. Set `is_verified = True`

**Response:**
```json
{
    "email": "Đã kích hoạt thành công"
}
```

**Errors:**
- `ExpiredSignatureError`: Token expired
- `DecodeError`: Invalid token

---

### Class: `ReSendMailVery`

```python
class ReSendMailVery(generics.GenericAPIView):
    """Re-send verification email."""
    
    serializer_class = ReSendMailVerySerializer
```

**URL:** `POST /api/auth/re-email-verify/`

**Request:**
```json
{
    "email": "user@example.com"
}
```

---

### Class: `LoginAPIView`

```python
class LoginAPIView(generics.GenericAPIView):
    """User login endpoint."""
    
    serializer_class = LoginSerializer
```

**URL:** `POST /api/auth/login/`

**Request:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "email": "user@example.com",
    "username": "username",
    "tokens": {
        "refresh": "<refresh-token>",
        "access": "<access-token>"
    }
}
```

---

### Class: `RequestPasswordResetEmail`

```python
class RequestPasswordResetEmail(generics.GenericAPIView):
    """Request password reset email."""
    
    serializer_class = ResetPasswordEmailRequestSerializer
```

**URL:** `POST /api/auth/request-reset-email/`

**Request:**
```json
{
    "email": "user@example.com"
}
```

**Process:**
1. Find user by email
2. Generate reset token
3. Send reset email

**Response:**
```json
{
    "success": "Chúng tôi đã gửi cho bạn một liên kết để đặt lại mật khẩu của bạn"
}
```

---

### Class: `PasswordTokenCheckAPI`

```python
class PasswordTokenCheckAPI(generics.GenericAPIView):
    """Validate password reset token."""
    
    serializer_class = SetNewPasswordSerializer
```

**URL:** `GET /api/auth/password-reset/<uidb64>/<token>/`

**Process:**
1. Decode user ID from uidb64
2. Validate token
3. Redirect with token validity status

---

### Class: `SetNewPasswordAPIView`

```python
class SetNewPasswordAPIView(generics.GenericAPIView):
    """Set new password endpoint."""
    
    serializer_class = SetNewPasswordSerializer
```

**URL:** `PATCH /api/auth/password-reset-complete`

**Request:**
```json
{
    "password": "newpassword123",
    "token": "<reset-token>",
    "uidb64": "<encoded-user-id>"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Đặt lại mật khẩu thành công"
}
```

---

### Class: `LogoutAPIView`

```python
class LogoutAPIView(generics.GenericAPIView):
    """User logout endpoint."""
    
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)
```

**URL:** `POST /api/auth/logout/`

**Request:**
```json
{
    "refresh": "<refresh-token>"
}
```

**Process:**
- Blacklist the refresh token

**Response:** `204 No Content`

---

## 4. Certificate Authentication Backends (`pki/auth/backends.py`)

### Class: `CertificateAuthenticationBackend`

```python
class CertificateAuthenticationBackend(BaseBackend):
    """
    Authentication backend that authenticates users via X.509 client certificates.
    
    Used when the user presents a client certificate during TLS handshake.
    """
```

#### Method: `authenticate`

```python
def authenticate(self, request, certificate_pem=None, 
                 certificate_fingerprint=None, **kwargs):
    """Authenticate a user based on their certificate."""
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `certificate_pem` | str | Certificate in PEM format |
| `certificate_fingerprint` | str | SHA-256 fingerprint |

**Process:**
1. Find certificate by fingerprint
2. Verify certificate is active
3. Verify certificate is within validity period
4. Check certificate can authenticate (`clientAuth` EKU)
5. Get associated user
6. Verify user is active
7. Record certificate usage
8. Log authentication success

**Returns:** `User` or `None`

---

### Class: `ChallengeResponseAuthBackend`

```python
class ChallengeResponseAuthBackend(BaseBackend):
    """
    Challenge-response authentication backend.
    
    Requires the client to sign a random challenge with their private key.
    """
```

#### Method: `generate_challenge`

```python
def generate_challenge(self, certificate):
    """Generate a random challenge for the certificate."""
```

**Returns:**
```python
{
    'challenge_id': 'uuid',
    'challenge_b64': '<base64-random-32-bytes>',
    'expires_at': datetime
}
```

#### Method: `authenticate`

```python
def authenticate(self, request, certificate_pem=None,
                 challenge=None, signature=None,
                 pq_signature=None, **kwargs):
    """Authenticate using challenge-response."""
```

**Process:**
1. Load and verify certificate
2. Find certificate in database
3. Verify classical signature of challenge
4. Verify PQ signature if provided and certificate has PQ key
5. Return user if all signatures valid

**Signature Verification:**
```python
# Classical (RSA/ECDSA)
ClassicalCrypto.verify_signature(public_key, signature_bytes, challenge_bytes)

# Post-Quantum (Dilithium)
PostQuantumCrypto.verify(pq_public_key, challenge_bytes, pq_sig_bytes, algorithm)
```

---

## 5. TLS Certificate Middleware (`pki/auth/middleware.py`)

### Class: `ClientCertificateMiddleware`

```python
class ClientCertificateMiddleware:
    """
    Middleware to extract client certificate from TLS connection.
    
    Works with reverse proxies (nginx, Apache) that pass certificate info
    via headers.
    """
```

**Headers Processed:**
- `X-SSL-CLIENT-CERT`: Full certificate (PEM)
- `X-SSL-CLIENT-VERIFY`: Verification status (SUCCESS, FAILED, NONE)
- `X-SSL-CLIENT-S-DN`: Subject DN
- `X-SSL-CLIENT-I-DN`: Issuer DN
- `X-SSL-CLIENT-SERIAL`: Serial number

**Process:**
1. Check for certificate headers
2. Parse and validate certificate
3. Attach to `request.client_cert`

**Request Attribute:**
```python
request.client_cert = {
    'verified': True,
    'certificate_pem': '-----BEGIN CERTIFICATE-----...',
    'subject_dn': 'CN=...',
    'issuer_dn': 'CN=...',
    'serial': 'ABC123...',
}
```

---

## 6. Email Utilities (`authentication/utils.py`)

### Class: `Util`

```python
class Util:
    """Email utility class."""
```

#### Method: `send_email`

```python
@staticmethod
def send_email(data):
    """Send an email."""
```

**Parameters:**
```python
data = {
    'email_subject': 'Subject',
    'email_body': 'Body text',
    'to_email': 'recipient@example.com'
}
```

**Implementation:**
```python
from django.core.mail import EmailMessage

email = EmailMessage(
    subject=data['email_subject'],
    body=data['email_body'],
    to=[data['to_email']]
)
email.send()
```

---

## 7. URL Configuration

```python
# backend/authentication/urls.py

from django.urls import path
from .views import (
    RegisterView, LoginAPIView, LogoutAPIView,
    VerifyEmail, ReSendMailVery,
    RequestPasswordResetEmail, PasswordTokenCheckAPI, SetNewPasswordAPIView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('login/', LoginAPIView.as_view(), name="login"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('email-verify/', VerifyEmail.as_view(), name="email-verify"),
    path('re-email-verify/', ReSendMailVery.as_view(), name="email-verifys"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('request-reset-email/', RequestPasswordResetEmail.as_view(), name="request-reset-email"),
    path('password-reset/<uidb64>/<token>/', PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('password-reset-complete', SetNewPasswordAPIView.as_view(), name='password-reset-complete')
]
```

---

## 8. Authentication Flow Diagrams

### Password Authentication Flow

```
┌──────────┐     POST /login      ┌──────────┐
│  Client  │ ──────────────────▶  │  Server  │
│          │  {email, password}   │          │
└──────────┘                      └──────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Validate Email  │
                              │   & Password    │
                              └─────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Check Verified  │
                              └─────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Generate JWT    │
                              │    Tokens       │
                              └─────────────────┘
                                       │
┌──────────┐  {access, refresh}  ◀─────┘
│  Client  │ ◀────────────────────────
└──────────┘
```

### Certificate Challenge-Response Flow

```
┌──────────┐  POST /auth/challenge    ┌──────────┐
│  Client  │ ──────────────────────▶  │  Server  │
│          │  {email, fingerprint}    │          │
└──────────┘                          └──────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Find Certificate│
                                  │   by Fingerprint│
                                  └─────────────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Generate Random │
                                  │    Challenge    │
                                  └─────────────────┘
                                           │
┌──────────┐  {challenge_id,      ◀────────┘
│  Client  │   challenge_b64}
└──────────┘
      │
      │  Sign challenge with private key
      │  (classical + PQ)
      ▼
┌──────────┐  POST /auth/verify       ┌──────────┐
│  Client  │ ──────────────────────▶  │  Server  │
│          │  {challenge_id,          │          │
│          │   classical_signature,   │          │
│          │   pq_signature}          │          │
└──────────┘                          └──────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Verify Classical│
                                  │   Signature     │
                                  └─────────────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Verify PQ       │
                                  │   Signature     │
                                  └─────────────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │ Generate JWT    │
                                  │    Tokens       │
                                  └─────────────────┘
                                           │
┌──────────┐  {access, refresh}   ◀────────┘
│  Client  │
└──────────┘
```

---

## 9. Security Considerations

### Password Security
- Passwords hashed with Django's PBKDF2
- Minimum password length enforced
- Password reset tokens expire

### Token Security
- JWT tokens with expiration
- Refresh tokens can be blacklisted
- Access tokens short-lived

### Certificate Authentication
- Certificate fingerprint verification
- Certificate validity period check
- Certificate status check (not revoked)
- Challenge-response prevents replay attacks
- Dual signature (classical + PQ) for hybrid security

### Email Verification
- Required before login
- Token-based verification
- Prevents unauthorized account use
