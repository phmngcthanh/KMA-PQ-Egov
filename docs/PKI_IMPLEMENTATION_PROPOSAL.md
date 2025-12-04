# E-Government PKI System - Implementation Proposal

**Project:** NT208 - Chính quyền điện tử PKI  
**Date:** December 3, 2025  
**Version:** 1.0  

---

## 1. Executive Summary

This document outlines the comprehensive implementation plan to transform the existing e-government paperwork system into a full-featured PKI (Public Key Infrastructure) solution with post-quantum cryptography support. The implementation will enable secure digital document signing, certificate-based authentication, and quantum-resistant security measures suitable for a master's course project.

---

## 2. Current System Analysis

### 2.1 Existing Components

| Component | Status | Location | Details |
|-----------|--------|----------|---------|
| **User Authentication** | ✅ Implemented | `backend/authentication/` | Email/password, JWT tokens, Google/Facebook OAuth |
| **User Model** | ✅ Implemented | `authentication/models.py` | Username, email, password, phone, verification |
| **Document Management** | ✅ Implemented | `backend/hoso/` | File upload, categories, status tracking |
| **PDF Signing (RSA)** | ⚠️ Partial | `backend/hoso/signpdf.py` | Uses OpenSSL with RSA-1024 (weak) |
| **PDF Signing (PQ)** | ⚠️ Prototype | `backend/signpdf.py` | Uses liboqs Dilithium3 (incomplete) |
| **Email Notifications** | ✅ Implemented | `authentication/utils.py` | Email verification, password reset |
| **Admin Dashboard** | ✅ Implemented | `frontend/src/container/AdminTemplate/` | Basic admin interface |

### 2.2 Current Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  Django API │────▶│  PostgreSQL │
│   (React)   │     │  (DRF+JWT)  │     │  Database   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       └───────────▶│ Social Auth │
                    │ Google/FB   │
                    └─────────────┘
```

### 2.3 Current PDF Signing Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  User       │────▶│  Upload PDF │────▶│  Sign with  │
│  Submits    │     │  Document   │     │  Global Key │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Email      │
                                        │  Signed PDF │
                                        └─────────────┘
```

### 2.4 Critical Gaps Identified

| Gap | Severity | Impact |
|-----|----------|--------|
| **No Certificate Authority** | 🔴 Critical | Cannot issue trusted certificates |
| **No Certificate Lifecycle Management** | 🔴 Critical | No revocation, renewal, or validation |
| **No Per-User Certificates** | 🔴 Critical | All documents signed with same key |
| **No Certificate-Based Authentication** | 🔴 Critical | Cannot login with smart card/certificate |
| **No Signature Verification** | 🔴 Critical | Cannot verify signed documents |
| **Weak RSA Keys (1024-bit)** | 🔴 Critical | Vulnerable to attacks |
| **No Post-Quantum in Production** | 🟠 High | Future quantum threat |
| **No HSM/Secure Key Storage** | 🟠 High | Keys stored in plaintext files |
| **No Audit Trail** | 🟠 High | No cryptographic logging |
| **No OCSP/CRL** | 🟠 High | Cannot check certificate status |

---

## 3. Proposed Architecture

### 3.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │
│  │ Login        │  │ Certificate  │  │ Document                 │ │
│  │ (Email/Cert) │  │ Management   │  │ Sign/Verify              │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                      BACKEND (Django REST)                         │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    PKI Application                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │
│  │  │ CA Service  │  │ Cert Service│  │ Crypto Module       │ │   │
│  │  │ - Root CA   │  │ - Issue     │  │ - Classical (RSA)   │ │   │
│  │  │ - Sub CA    │  │ - Revoke    │  │ - Post-Quantum      │ │   │
│  │  │ - CRL/OCSP  │  │ - Renew     │  │ - Hybrid Signing    │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │
│  │ Authentication │  │ Hoso (Docs)    │  │ Social Auth        │   │
│  │ + Cert Auth    │  │ + PDF Signing  │  │                    │   │
│  └────────────────┘  └────────────────┘  └────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │
│  │ PostgreSQL     │  │ File Storage   │  │ Key Storage        │   │
│  │ - Users        │  │ - Documents    │  │ - CA Keys (enc)    │   │
│  │ - Certificates │  │ - Signed PDFs  │  │ - User Keys        │   │
│  │ - CRL Records  │  │               │  │                    │   │
│  └────────────────┘  └────────────────┘  └────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Certificate Hierarchy

```
                    ┌─────────────────────────┐
                    │      ROOT CA            │
                    │  "E-Gov Root CA"        │
                    │  Validity: 20 years     │
                    │  Algorithm: Hybrid      │
                    │  (RSA-4096 + Dilithium) │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  OFFICER SUB-CA   │ │  CITIZEN SUB-CA   │ │  SERVICE SUB-CA   │
│  Validity: 10 yrs │ │  Validity: 10 yrs │ │  Validity: 5 yrs  │
│  For: Gov Staff   │ │  For: Citizens    │ │  For: Services    │
└─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
          │                     │                     │
          ▼                     ▼                     ▼
    ┌───────────┐         ┌───────────┐         ┌───────────┐
    │ Officer   │         │ Citizen   │         │ Service   │
    │ Certs     │         │ Certs     │         │ Certs     │
    │ 2 years   │         │ 3 years   │         │ 1 year    │
    └───────────┘         └───────────┘         └───────────┘
```

### 3.3 Post-Quantum Strategy

We will implement **hybrid cryptography** to ensure both current security and quantum resistance:

| Operation | Classical Algorithm | Post-Quantum Algorithm | Hybrid Approach |
|-----------|---------------------|------------------------|-----------------|
| **Digital Signatures** | RSA-4096 or ECDSA P-384 | Dilithium3 (ML-DSA) | Dual signature |
| **Key Exchange** | ECDH P-384 | Kyber768 (ML-KEM) | Composite key |
| **Hashing** | SHA-256 | SHA-3-256 | SHA-3-256 preferred |

**Library Choice: liboqs (Open Quantum Safe)**
- NIST standardized algorithms (Dilithium, Kyber)
- Python bindings available (`pip install oqs`)
- Active development and maintenance
- Already partially integrated in existing code

---

## 4. Implementation Phases

### Phase 1: PKI Foundation (Week 1-2)

**Deliverables:**
- [ ] Create `pki` Django application
- [ ] Implement CA models (Root, Intermediate)
- [ ] Implement Certificate models
- [ ] Implement CRL/OCSP models
- [ ] Create CA management service
- [ ] Create certificate issuance service

**Files to Create:**
```
backend/pki/
├── __init__.py
├── admin.py
├── apps.py
├── models/
│   ├── __init__.py
│   ├── ca.py
│   ├── certificate.py
│   └── revocation.py
├── services/
│   ├── __init__.py
│   ├── ca_service.py
│   └── cert_service.py
├── serializers.py
├── views.py
├── urls.py
└── migrations/
```

### Phase 2: Cryptographic Module (Week 2-3)

**Deliverables:**
- [ ] Classical crypto operations (RSA, ECDSA)
- [ ] Post-quantum operations (Dilithium, Kyber)
- [ ] Hybrid signature generation
- [ ] Hybrid signature verification
- [ ] Key generation utilities

**Files to Create:**
```
backend/pki/crypto/
├── __init__.py
├── classical.py      # RSA/ECDSA operations
├── post_quantum.py   # Dilithium/Kyber operations
├── hybrid.py         # Combined crypto
└── utils.py          # Helper functions
```

### Phase 3: PDF Signing Enhancement (Week 3-4)

**Deliverables:**
- [ ] User-specific certificate signing
- [ ] Certificate chain embedding
- [ ] Post-quantum PDF signatures
- [ ] Signature verification API
- [ ] Long-term validation support

**Files to Modify/Create:**
```
backend/pki/
├── services/
│   └── pdf_service.py    # New PDF signing service
backend/hoso/
├── views.py              # Modify signing endpoints
```

### Phase 4: Certificate-Based Authentication (Week 4-5)

**Deliverables:**
- [ ] Client certificate extraction middleware
- [ ] Certificate authentication backend
- [ ] Map certificates to user accounts
- [ ] Dual login support (password + certificate)
- [ ] API endpoints for cert login

**Files to Create:**
```
backend/pki/auth/
├── __init__.py
├── backends.py      # Custom auth backend
└── middleware.py    # TLS client cert extraction
```

### Phase 5: Frontend Integration (Week 5-6)

**Deliverables:**
- [ ] Certificate request form
- [ ] Certificate download/export
- [ ] Certificate status viewer
- [ ] Document verification UI
- [ ] Certificate-based login option

**Files to Create:**
```
frontend/src/
├── container/HomeTemplate/
│   ├── CertificateManagement/
│   │   ├── index.js
│   │   ├── RequestCertificate.js
│   │   ├── MyCertificates.js
│   │   └── VerifyDocument.js
│   ├── ManagerUser/Login/
│   │   └── CertLogin.js
```

---

## 5. Data Models

### 5.1 Certificate Authority Model

```python
class CertificateAuthority(models.Model):
    CA_TYPES = [
        ('ROOT', 'Root CA'),
        ('INTERMEDIATE_OFFICER', 'Officer Intermediate CA'),
        ('INTERMEDIATE_CITIZEN', 'Citizen Intermediate CA'),
        ('INTERMEDIATE_SERVICE', 'Service Intermediate CA'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    common_name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    organizational_unit = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, default='VN')
    
    ca_type = models.CharField(max_length=30, choices=CA_TYPES)
    parent_ca = models.ForeignKey('self', null=True, blank=True, 
                                   on_delete=models.PROTECT)
    
    # Classical cryptography
    certificate_pem = models.TextField()
    private_key_pem_encrypted = models.BinaryField()
    public_key_pem = models.TextField()
    
    # Post-quantum cryptography
    pq_algorithm = models.CharField(max_length=50, default='Dilithium3')
    pq_public_key = models.BinaryField(null=True)
    pq_private_key_encrypted = models.BinaryField(null=True)
    
    serial_number = models.CharField(max_length=64, unique=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # CRL settings
    crl_distribution_point = models.URLField(blank=True)
    next_crl_update = models.DateTimeField(null=True)
```

### 5.2 User Certificate Model

```python
class UserCertificate(models.Model):
    CERT_TYPES = [
        ('OFFICER', 'Government Officer'),
        ('CITIZEN', 'Citizen'),
        ('SERVICE', 'Service Account'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('REVOKED', 'Revoked'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    user = models.ForeignKey('authentication.User', 
                             on_delete=models.CASCADE,
                             related_name='certificates')
    issuing_ca = models.ForeignKey(CertificateAuthority,
                                    on_delete=models.PROTECT)
    
    cert_type = models.CharField(max_length=20, choices=CERT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='PENDING')
    
    # Certificate data
    serial_number = models.CharField(max_length=64, unique=True)
    certificate_pem = models.TextField()
    public_key_pem = models.TextField()
    
    # Post-quantum
    pq_public_key = models.BinaryField(null=True)
    pq_algorithm = models.CharField(max_length=50, default='Dilithium3')
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Revocation
    revoked_at = models.DateTimeField(null=True)
    revocation_reason = models.CharField(max_length=255, blank=True)
    
    # Metadata
    subject_dn = models.CharField(max_length=500)
    fingerprint_sha256 = models.CharField(max_length=64)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 5.3 Certificate Revocation Model

```python
class CertificateRevocationList(models.Model):
    issuing_ca = models.ForeignKey(CertificateAuthority,
                                    on_delete=models.CASCADE)
    crl_number = models.IntegerField()
    this_update = models.DateTimeField()
    next_update = models.DateTimeField()
    crl_pem = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)

class RevokedCertificate(models.Model):
    REVOCATION_REASONS = [
        ('UNSPECIFIED', 'Unspecified'),
        ('KEY_COMPROMISE', 'Key Compromise'),
        ('CA_COMPROMISE', 'CA Compromise'),
        ('AFFILIATION_CHANGED', 'Affiliation Changed'),
        ('SUPERSEDED', 'Superseded'),
        ('CESSATION_OF_OPERATION', 'Cessation of Operation'),
        ('CERTIFICATE_HOLD', 'Certificate Hold'),
        ('PRIVILEGE_WITHDRAWN', 'Privilege Withdrawn'),
    ]
    
    certificate = models.OneToOneField(UserCertificate,
                                        on_delete=models.CASCADE)
    revocation_date = models.DateTimeField()
    reason = models.CharField(max_length=30, choices=REVOCATION_REASONS)
    crl = models.ForeignKey(CertificateRevocationList,
                            on_delete=models.SET_NULL, null=True)
```

---

## 6. API Endpoints

### 6.1 CA Management (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pki/ca/create-root/` | Create Root CA |
| POST | `/api/pki/ca/create-intermediate/` | Create Intermediate CA |
| GET | `/api/pki/ca/` | List all CAs |
| GET | `/api/pki/ca/{id}/` | Get CA details |
| POST | `/api/pki/ca/{id}/generate-crl/` | Generate CRL |

### 6.2 Certificate Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pki/certificates/request/` | Request new certificate |
| GET | `/api/pki/certificates/my/` | Get user's certificates |
| GET | `/api/pki/certificates/{id}/` | Get certificate details |
| GET | `/api/pki/certificates/{id}/download/` | Download certificate |
| POST | `/api/pki/certificates/{id}/revoke/` | Revoke certificate |
| GET | `/api/pki/certificates/verify/` | Verify a certificate |

### 6.3 Document Signing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/pki/sign/pdf/` | Sign PDF with user certificate |
| POST | `/api/pki/verify/pdf/` | Verify PDF signature |
| GET | `/api/pki/sign/history/` | Get signing history |

### 6.4 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/certificate/` | Login with client certificate |
| POST | `/api/auth/login/` | Login with email/password (existing) |

---

## 7. Security Considerations

### 7.1 Key Protection

| Key Type | Storage Method | Encryption |
|----------|---------------|------------|
| Root CA Private Key | Database (encrypted) | AES-256-GCM with master key |
| Intermediate CA Keys | Database (encrypted) | AES-256-GCM |
| User Private Keys | Client-side only | PKCS#8 with password |

### 7.2 Post-Quantum Readiness

- All new certificates include hybrid signatures
- Signature verification accepts both classical and PQ signatures
- Migration path for existing certificates
- Algorithm agility for future updates

### 7.3 Audit Logging

All PKI operations will be logged:
- Certificate issuance
- Certificate revocation
- Signature operations
- Authentication events

---

## 8. Dependencies

### 8.1 New Python Packages

```
# Post-quantum cryptography
liboqs-python>=0.9.0

# Enhanced cryptography
cryptography>=41.0.0
pyOpenSSL>=23.0.0

# PDF operations (keep existing)
PDFNetPython3>=9.1.0

# Additional utilities
python-dateutil>=2.8.0
```

### 8.2 Frontend Packages

```
# Certificate handling
node-forge>=1.3.0

# File handling
file-saver>=2.0.5
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

- CA creation and management
- Certificate issuance
- Signature generation/verification
- Authentication backends

### 9.2 Integration Tests

- Full certificate lifecycle
- PDF signing workflow
- Login with certificate

### 9.3 Security Tests

- Key generation strength
- Signature verification
- Certificate chain validation

---

## 10. Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | PKI Foundation | Models, CA service, basic APIs |
| 2-3 | Crypto Module | Classical + PQ operations |
| 3-4 | PDF Signing | Enhanced signing with user certs |
| 4-5 | Cert Authentication | Login with certificate |
| 5-6 | Frontend | UI for certificate management |
| 6 | Testing & Documentation | Complete testing, docs |

---

## 11. Success Criteria

- [ ] Root CA and Intermediate CAs operational
- [ ] Officers can request and receive certificates
- [ ] Citizens can request and receive certificates
- [ ] PDFs signed with user-specific certificates
- [ ] PDF signatures verifiable
- [ ] Post-quantum signatures implemented
- [ ] Certificate-based login functional
- [ ] CRL generation and distribution working
- [ ] Full audit trail implemented

---

## 12. References

- [NIST Post-Quantum Cryptography](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [Open Quantum Safe Project](https://openquantumsafe.org/)
- [RFC 5280 - X.509 PKI Certificate](https://tools.ietf.org/html/rfc5280)
- [RFC 6960 - OCSP](https://tools.ietf.org/html/rfc6960)
- [Django REST Framework](https://www.django-rest-framework.org/)

---

*Document prepared for NT208 - Electronic Government PKI Master Course Project*
