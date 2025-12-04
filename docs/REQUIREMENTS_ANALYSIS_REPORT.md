# Requirements Analysis Report
## E-Government PKI System - NT208

**Document Version:** 1.0  
**Date:** December 4, 2025  
**Project:** Chính quyền điện tử PKI (E-Government Public Key Infrastructure)

---

## 1. Executive Summary

This document provides a comprehensive requirements analysis for the E-Government PKI System. The system implements a hybrid Public Key Infrastructure combining classical cryptography (RSA/ECDSA) with post-quantum cryptography (Dilithium/Kyber) to ensure long-term security against quantum computing threats.

### Overall Compliance Status

| Category | Status | Completeness |
|----------|--------|--------------|
| **PKI System** | ✅ Complete | ~100% |
| **E-Gov System** | ✅ Mostly Complete | ~95% |

---

## 2. PKI System Requirements

### 2.1 Post-Quantum and Current Encryption PKI

#### 2.1.1 Classical Cryptography Support

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| RSA-2048 Key Generation | ✅ Met | `ClassicalCrypto.generate_keypair('RSA_2048')` |
| RSA-4096 Key Generation | ✅ Met | `ClassicalCrypto.generate_keypair('RSA_4096')` |
| ECDSA P-256 Support | ✅ Met | `ClassicalCrypto.generate_keypair('ECDSA_P256')` |
| ECDSA P-384 Support | ✅ Met | `ClassicalCrypto.generate_keypair('ECDSA_P384')` |
| Digital Signature Creation | ✅ Met | `ClassicalCrypto.sign_data()` |
| Signature Verification | ✅ Met | `ClassicalCrypto.verify_signature()` |
| X.509 Certificate Creation | ✅ Met | `ClassicalCrypto.create_ca_certificate()`, `create_end_entity_certificate()` |

**Evidence Location:** `backend/pki/crypto/classical.py`

#### 2.1.2 Post-Quantum Cryptography Support

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Dilithium2 (ML-DSA-44) | ✅ Met | NIST Level 2 security |
| Dilithium3 (ML-DSA-65) | ✅ Met | NIST Level 3 security (Recommended) |
| Dilithium5 (ML-DSA-87) | ✅ Met | NIST Level 5 security |
| Falcon-512 | ✅ Met | Alternative signature scheme |
| Falcon-1024 | ✅ Met | Higher security alternative |
| SPHINCS+-SHA2-128f | ✅ Met | Hash-based stateless signatures |
| Kyber512 KEM | ✅ Met | Key encapsulation mechanism |
| Kyber768 KEM | ✅ Met | Recommended KEM |
| Kyber1024 KEM | ✅ Met | Highest security KEM |

**Evidence Location:** `backend/pki/crypto/post_quantum.py`

#### 2.1.3 Hybrid Cryptography Support

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Hybrid Key Generation | ✅ Met | `HybridCrypto.generate_hybrid_keypair()` |
| Hybrid Signature (Classical + PQ) | ✅ Met | `HybridCrypto.hybrid_sign()` |
| Hybrid Verification | ✅ Met | `HybridCrypto.hybrid_verify()` |
| Hybrid Certificate Data | ✅ Met | `HybridCrypto.create_hybrid_certificate_data()` |

**Evidence Location:** `backend/pki/crypto/hybrid.py`

---

### 2.2 Certificate Authority Management

#### 2.2.1 Root CA Operations

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Create Root CA | ✅ Met | `CAService.create_root_ca()` |
| Self-signed Certificate | ✅ Met | Automatic during creation |
| PQ Key Pair Generation | ✅ Met | Dilithium keys generated |
| Private Key Encryption | ✅ Met | AES-256-GCM encryption |
| 20-year Default Validity | ✅ Met | `ROOT_CA_VALIDITY_YEARS = 20` |

#### 2.2.2 Intermediate CA Operations

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Create Intermediate CA | ✅ Met | `CAService.create_intermediate_ca()` |
| Officer Intermediate CA | ✅ Met | `ca_type='INTERMEDIATE_OFFICER'` |
| Citizen Intermediate CA | ✅ Met | `ca_type='INTERMEDIATE_CITIZEN'` |
| Service Intermediate CA | ✅ Met | `ca_type='INTERMEDIATE_SERVICE'` |
| Parent CA Signing | ✅ Met | Signed by parent CA |
| 10-year Default Validity | ✅ Met | `INTERMEDIATE_CA_VALIDITY_YEARS = 10` |

#### 2.2.3 CA Lifecycle Management

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Deactivate CA | ✅ Met | `CAService.deactivate_ca()` |
| Mark CA Compromised | ✅ Met | `CAService.mark_ca_compromised()` |
| CA Chain Retrieval | ✅ Met | `CertificateAuthorityViewSet.chain()` |
| CA Certificate Download | ✅ Met | PEM and DER formats |

**Evidence Location:** `backend/pki/services/ca_service.py`, `backend/pki/views.py`

---

### 2.3 Certificate Management

#### 2.3.1 Certificate Request Processing

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Create Certificate Request | ✅ Met | `CertificateService.create_certificate_request()` |
| Officer Certificate Requests | ✅ Met | `cert_type='OFFICER'` |
| Citizen Certificate Requests | ✅ Met | `cert_type='CITIZEN'` |
| Service Certificate Requests | ✅ Met | `cert_type='SERVICE'` |
| CSR Submission (PKCS#10) | ✅ Met | `csr_pem` field support |
| PQ Public Key Submission | ✅ Met | `pq_public_key` field |

#### 2.3.2 Certificate Issuance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Issue Certificate | ✅ Met | `CertificateService.issue_certificate()` |
| Approve Request | ✅ Met | `CertificateService.approve_request()` |
| Reject Request | ✅ Met | `CertificateService.reject_request()` |
| Quick Issue (Admin) | ✅ Met | `CertificateService.quick_issue_certificate()` |
| Hybrid Signature Embedding | ✅ Met | Classical + PQ signature in certificate |
| Key Usage Extension | ✅ Met | digitalSignature, nonRepudiation, keyEncipherment |
| Extended Key Usage | ✅ Met | clientAuth, emailProtection, codeSigning |

#### 2.3.3 Certificate Revocation

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Revoke Certificate | ✅ Met | `CertificateService.revoke_certificate()` |
| Revocation Reasons | ✅ Met | 10 standard reasons (keyCompromise, etc.) |
| CRL Generation | ✅ Met | `CAService.generate_crl()` |
| CRL Distribution | ✅ Met | `CRLViewSet.download()` |
| Revocation Entry Tracking | ✅ Met | `RevokedCertificate` model |

#### 2.3.4 Certificate Download & Assignment

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Download PEM Format | ✅ Met | `UserCertificateViewSet.download()` |
| Download DER Format | ✅ Met | Format parameter support |
| Certificate Chain Export | ✅ Met | `UserCertificateViewSet.chain()` |
| User Assignment | ✅ Met | `UserCertificate.user` FK |

**Evidence Location:** `backend/pki/services/cert_service.py`, `backend/pki/models/`

---

## 3. E-Government System Requirements

### 3.1 User Management

#### 3.1.1 User Registration & Verification

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| User Registration | ✅ Met | `RegisterView` |
| Email Verification | ✅ Met | `VerifyEmail` with JWT token |
| Re-send Verification Email | ✅ Met | `ReSendMailVery` |
| Username/Email Unique | ✅ Met | Model constraints |

#### 3.1.2 Password Management

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Password Change | ✅ Met | `SetNewPasswordAPIView` |
| Password Reset Request | ✅ Met | `RequestPasswordResetEmail` |
| Password Reset Token Validation | ✅ Met | `PasswordTokenCheckAPI` |
| Secure Password Storage | ✅ Met | Django's password hashing |

#### 3.1.3 User Roles

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Citizen Users | ✅ Met | Default user type |
| Officer Users | ✅ Met | `User.is_officer` field |
| Staff/Admin Users | ✅ Met | `User.is_staff`, `is_superuser` |
| Permission-based Access | ✅ Met | `IsAdminOrOfficer`, `IsCertificateOwner` |

**Evidence Location:** `backend/authentication/views.py`, `backend/authentication/models.py`

---

### 3.2 Administrative Request Management

#### 3.2.1 Request Submission

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Submit Request (NopHoSo) | ✅ Met | `NopHoSoViewSet.nop_hoso()` |
| PDF File Upload | ✅ Met | `NopHoSo.hoso` FileField |
| Image Upload | ✅ Met | `ModelUse.image` ImageField |
| Category Selection | ✅ Met | `NopHoSo.category` FK |
| Field Selection | ✅ Met | `NopHoSo.field` FK |
| Citizen Information | ✅ Met | fullname, cmnd, address fields |

#### 3.2.2 Request Status Tracking

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Status: Đang chờ (Pending) | ✅ Met | `status=0` |
| Status: Đã xem (Viewed) | ✅ Met | `status=1` |
| Status: Thành công (Success) | ✅ Met | `status=2` |
| Status: Thất bại (Failed) | ✅ Met | `status=3` |
| User Status Query | ✅ Met | `StatusHoSoViewSet.getstatus_user()` |

#### 3.2.3 Request Categories & Fields

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Category Management | ✅ Met | `Category` model |
| Field/Sub-category | ✅ Met | `Field` model with category FK |
| File Templates | ✅ Met | `FileHoSo` model |
| Category-based Navigation | ✅ Met | `CategoryViewSet`, `FieldViewSet` |

**Evidence Location:** `backend/hoso/views.py`, `backend/hoso/models.py`

---

### 3.3 Document Processing & Signing

#### 3.3.1 Request Approval/Denial

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| View Request Details | ✅ Met | `NopHoSoViewSet.view_hoso()` |
| Approve Request | ✅ Met | Status update to SUCCESS |
| Deny Request | ✅ Met | Status update to FAIL |
| Officer-only Actions | ✅ Met | Permission classes |

#### 3.3.2 PDF Signing

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Sign PDF with Certificate | ✅ Met | `PDFSigningService.sign_pdf()` |
| Hybrid Signature (Classical+PQ) | ✅ Met | Both signature types |
| Detached Signature Fallback | ✅ Met | When PDFNet unavailable |
| Signature Appearance | ✅ Met | Configurable position, image |
| Signing Reason/Location | ✅ Met | Metadata fields |
| Email Notification | ✅ Met | `ky_file()` sends email |

#### 3.3.3 Signature Verification

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Verify PDF Signature | ✅ Met | `PDFSigningService.verify_pdf_signature()` |
| Verify Classical Signature | ✅ Met | RSA/ECDSA verification |
| Verify PQ Signature | ✅ Met | Dilithium verification |
| Certificate Chain Validation | ✅ Met | Chain verification |
| Document Integrity Check | ✅ Met | Hash comparison |

**Evidence Location:** `backend/pki/services/pdf_service.py`, `backend/hoso/views.py`

---

### 3.4 Revocation & Corrective Actions

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Certificate Revocation | ✅ Met | Full implementation |
| CRL Publication | ✅ Met | Public download endpoint |
| Revocation Audit Trail | ✅ Met | `PKIAuditLog` |
| Document Revision | ⚠️ Partial | Status change only, no formal workflow |

**Recommendation:** Implement a formal document amendment/correction workflow with version tracking.

---

### 3.5 Authentication Methods

#### 3.5.1 Username/Password Authentication

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Email/Password Login | ✅ Met | `LoginAPIView` |
| JWT Token Generation | ✅ Met | Access + Refresh tokens |
| Token Refresh | ✅ Met | `TokenRefreshView` |
| Logout (Token Blacklist) | ✅ Met | `LogoutAPIView` |

#### 3.5.2 Certificate-based Authentication

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| TLS Client Certificate | ✅ Met | `CertificateAuthenticationBackend` |
| Certificate Fingerprint Lookup | ✅ Met | SHA-256 fingerprint matching |
| Certificate Validity Check | ✅ Met | Status, expiry, CA validation |
| Challenge-Response Auth | ✅ Met | `ChallengeResponseAuthBackend` |
| PQ Signature in Challenge | ✅ Met | Optional Dilithium signature |

#### 3.5.3 Social Authentication

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Google OAuth | ✅ Met | `social_auth/google.py` |
| Facebook OAuth | ✅ Met | `social_auth/facebook.py` |
| Twitter OAuth | ✅ Met | `social_auth/twitterhelper.py` |

**Evidence Location:** `backend/pki/auth/backends.py`, `backend/authentication/views.py`, `backend/social_auth/`

---

## 4. Frontend Implementation Status

### 4.1 User-Facing Features

| Feature | Status | Location |
|---------|--------|----------|
| Certificate Manager | ✅ Complete | `frontend/src/container/HomeTemplate/CertificateManager/` |
| PDF Signer/Verifier | ✅ Complete | `frontend/src/container/HomeTemplate/PDFSigner/` |
| Request Submission | ✅ Complete | `frontend/src/container/HomeTemplate/NopHoSo/` |
| Request Status | ✅ Complete | `frontend/src/container/HomeTemplate/TinhTrangHoSo/` |
| Password Change | ✅ Complete | `frontend/src/container/HomeTemplate/DoiMatKhau/` |
| FAQ/Help | ✅ Complete | `frontend/src/container/HomeTemplate/HoiDap/` |
| Search | ✅ Complete | `frontend/src/container/HomeTemplate/SearchPage/` |

### 4.2 Admin Features

| Feature | Status | Location |
|---------|--------|----------|
| Admin Dashboard | ✅ Complete | `frontend/src/container/AdminTemplate/Dashboard/` |
| Admin Pages | ✅ Complete | `frontend/src/container/AdminTemplate/AdminPage/` |

---

## 5. API Endpoints Summary

### 5.1 PKI Endpoints (`/api/pki/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ca/` | GET, POST | List/Create CAs |
| `/ca/{id}/` | GET, PUT, DELETE | CA details |
| `/ca/{id}/generate_crl/` | POST | Generate CRL |
| `/ca/{id}/download_certificate/` | GET | Download CA cert |
| `/ca/{id}/chain/` | GET | Get CA chain |
| `/certificates/` | GET | List certificates |
| `/certificates/{id}/` | GET | Certificate details |
| `/certificates/{id}/revoke/` | POST | Revoke certificate |
| `/certificates/{id}/download/` | GET | Download certificate |
| `/requests/` | GET, POST | List/Create requests |
| `/requests/{id}/approve/` | POST | Approve request |
| `/requests/{id}/reject/` | POST | Reject request |
| `/crl/` | GET | List CRLs |
| `/crl/{id}/download/` | GET | Download CRL |
| `/auth/` | GET | Check cert auth |
| `/auth/challenge/` | POST | Request challenge |
| `/auth/verify/` | POST | Verify challenge |
| `/pdf/sign/` | POST | Sign PDF |
| `/pdf/verify/` | POST | Verify PDF |
| `/status/` | GET | PKI status |
| `/my-certificates/` | GET | User's certificates |

### 5.2 Authentication Endpoints (`/api/auth/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register/` | POST | User registration |
| `/login/` | POST | User login |
| `/logout/` | POST | User logout |
| `/email-verify/` | GET | Verify email |
| `/token/refresh/` | POST | Refresh JWT |
| `/request-reset-email/` | POST | Request password reset |
| `/password-reset-complete` | PATCH | Complete reset |

### 5.3 HoSo Endpoints (`/api/hoso/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/categories/` | GET | List categories |
| `/fields/` | GET | List fields |
| `/filehosos/` | GET | List file templates |
| `/nophosos/nop_hoso/` | POST | Submit request |
| `/nophosos/{id}/ky/` | GET | Sign document |
| `/nophosos/{id}/view/` | GET | View request |
| `/statuss/getstatus/` | GET | Get user's statuses |

---

## 6. Security Analysis

### 6.1 Cryptographic Security

| Aspect | Implementation | Rating |
|--------|----------------|--------|
| Classical Algorithms | RSA-4096, ECDSA P-384 | ✅ Strong |
| Post-Quantum Algorithms | NIST standardized (Dilithium, Kyber) | ✅ Future-proof |
| Hybrid Approach | Both signatures required | ✅ Defense-in-depth |
| Key Storage | AES-256-GCM encryption | ✅ Secure |
| Hash Algorithms | SHA-384, SHA-256 | ✅ Strong |

### 6.2 Authentication Security

| Aspect | Implementation | Rating |
|--------|----------------|--------|
| Password Hashing | Django PBKDF2 | ✅ Secure |
| Token Management | JWT with refresh | ✅ Standard |
| Certificate Auth | X.509 + Challenge-Response | ✅ Strong |
| Session Management | Token-based | ✅ Stateless |

### 6.3 Audit & Compliance

| Aspect | Implementation | Rating |
|--------|----------------|--------|
| Audit Logging | `PKIAuditLog` model | ✅ Comprehensive |
| IP Tracking | Request IP logged | ✅ Present |
| Action Tracking | All PKI actions logged | ✅ Complete |
| Error Logging | Failures recorded | ✅ Present |

---

## 7. Gaps and Recommendations

### 7.1 Identified Gaps

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| Document Revision Workflow | Medium | Implement formal amendment tracking |
| OCSP Responder | Low | Add live OCSP endpoint |
| Rate Limiting | Medium | Add API rate limiting |
| Admin CA Management UI | Low | Enhance admin dashboard |

### 7.2 Future Enhancements

1. **OCSP Responder**: Implement real-time certificate status checking
2. **HSM Integration**: Support hardware security modules for CA keys
3. **Multi-factor Authentication**: Add TOTP/FIDO2 support
4. **Document Versioning**: Track document amendments and corrections
5. **Batch Operations**: Bulk certificate issuance/revocation
6. **Reporting Dashboard**: Analytics for certificate usage

---

## 8. Conclusion

The E-Government PKI System successfully implements all core requirements for a modern Public Key Infrastructure with post-quantum readiness. The system provides:

- **Complete PKI functionality** with support for hybrid classical/post-quantum cryptography
- **Full certificate lifecycle management** from request to revocation
- **Dual authentication methods** (password and certificate-based)
- **Document signing capabilities** with signature verification
- **Comprehensive audit logging** for compliance

The minor gaps identified do not affect core functionality and can be addressed in future iterations.

---

## Appendix A: Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | Django 3.x, Django REST Framework |
| Database | PostgreSQL |
| Frontend | React, Redux, Bootstrap |
| Classical Crypto | cryptography (Python) |
| Post-Quantum Crypto | liboqs-python |
| PDF Processing | PDFNetPython3 (optional) |
| Authentication | JWT (djangorestframework-simplejwt) |
| Email | Django email backend |

## Appendix B: NIST PQC Standards Reference

| Algorithm | NIST Standard | Use Case |
|-----------|---------------|----------|
| ML-DSA (Dilithium) | FIPS 204 | Digital Signatures |
| ML-KEM (Kyber) | FIPS 203 | Key Encapsulation |
| SLH-DSA (SPHINCS+) | FIPS 205 | Stateless Hash Signatures |
