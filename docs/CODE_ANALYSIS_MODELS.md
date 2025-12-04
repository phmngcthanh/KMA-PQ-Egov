# Code Analysis: PKI Models Module
## E-Government PKI System - NT208

**Module:** `backend/pki/models/`  
**Version:** 1.0  
**Date:** December 4, 2025

---

## Overview

The models module defines the database schema for PKI operations, including Certificate Authorities, user certificates, certificate requests, and revocation data.

### Module Structure

```
backend/pki/models/
├── __init__.py          # Model exports
├── ca.py                # Certificate Authority model
├── certificate.py       # User certificates and requests
├── revocation.py        # CRL and revocation entries
└── audit.py             # Audit logging model
```

---

## 1. Certificate Authority Model (`ca.py`)

### Class: `CertificateAuthority`

Represents a Certificate Authority in the PKI hierarchy.

```python
class CertificateAuthority(models.Model):
    """
    Certificate Authority model supporting both classical and post-quantum cryptography.
    
    Hierarchy:
    - ROOT: Self-signed root CA (offline, highly protected)
    - INTERMEDIATE_OFFICER: Issues certificates to government officers
    - INTERMEDIATE_CITIZEN: Issues certificates to citizens
    - INTERMEDIATE_SERVICE: Issues certificates for system services
    """
```

#### Choice Fields

```python
CA_TYPES = [
    ('ROOT', 'Root CA'),
    ('INTERMEDIATE_OFFICER', 'Officer Intermediate CA'),
    ('INTERMEDIATE_CITIZEN', 'Citizen Intermediate CA'),
    ('INTERMEDIATE_SERVICE', 'Service Intermediate CA'),
]

KEY_ALGORITHMS = [
    ('RSA_2048', 'RSA 2048-bit'),
    ('RSA_4096', 'RSA 4096-bit'),
    ('ECDSA_P256', 'ECDSA P-256'),
    ('ECDSA_P384', 'ECDSA P-384'),
]

PQ_ALGORITHMS = [
    ('DILITHIUM2', 'Dilithium2 (NIST Level 2)'),
    ('DILITHIUM3', 'Dilithium3 (NIST Level 3)'),
    ('DILITHIUM5', 'Dilithium5 (NIST Level 5)'),
    ('FALCON512', 'Falcon-512'),
    ('FALCON1024', 'Falcon-1024'),
]
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Primary key |
| `name` | CharField(255) | Unique CA name |
| `common_name` | CharField(255) | Certificate CN |
| `organization` | CharField(255) | Organization name |
| `organizational_unit` | CharField(255) | OU name |
| `locality` | CharField(255) | City |
| `state` | CharField(255) | State/Province |
| `country` | CharField(2) | Country code (default: VN) |
| `email` | EmailField | Contact email |

**Hierarchy Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ca_type` | CharField(30) | CA type from CA_TYPES |
| `parent_ca` | ForeignKey(self) | Parent CA (null for root) |
| `path_length` | IntegerField | Max subordinate CA depth |

**Classical Cryptography Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `key_algorithm` | CharField(20) | Classical algorithm |
| `certificate_pem` | TextField | X.509 certificate (PEM) |
| `private_key_pem_encrypted` | BinaryField | Encrypted private key |
| `public_key_pem` | TextField | Public key (PEM) |

**Post-Quantum Cryptography Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `pq_algorithm` | CharField(30) | PQ algorithm |
| `pq_public_key` | BinaryField | PQ public key |
| `pq_private_key_encrypted` | BinaryField | Encrypted PQ private key |
| `pq_certificate_extension` | TextField | PQ extension data |

**Validity Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `serial_number` | CharField(64) | Certificate serial |
| `valid_from` | DateTimeField | Not before |
| `valid_until` | DateTimeField | Not after |

**Status Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `is_active` | BooleanField | CA is operational |
| `is_compromised` | BooleanField | Security incident flag |

**Statistics Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `certificates_issued` | IntegerField | Total certs issued |
| `last_crl_number` | IntegerField | Last CRL sequence |
| `crl_validity_days` | IntegerField | CRL validity period |
| `max_cert_validity_days` | IntegerField | Max cert validity |

**CRL Distribution:**

| Field | Type | Description |
|-------|------|-------------|
| `crl_distribution_point` | URLField | CRL download URL |

**Timestamps:**

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | DateTimeField | Creation time |
| `updated_at` | DateTimeField | Last update time |

#### Methods

##### `is_valid()`

```python
def is_valid(self) -> bool:
    """Check if CA is currently valid and operational"""
```

**Returns:** `True` if:
- `is_active` is True
- `is_compromised` is False
- Current time is within validity period

##### `can_issue_certificate(cert_type)`

```python
def can_issue_certificate(self, cert_type: str) -> bool:
    """Check if this CA can issue a specific certificate type"""
```

**Mapping:**
| cert_type | Required ca_type |
|-----------|-----------------|
| `OFFICER` | `INTERMEDIATE_OFFICER` |
| `CITIZEN` | `INTERMEDIATE_CITIZEN` |
| `SERVICE` | `INTERMEDIATE_SERVICE` |

##### `subject_dn`

```python
@property
def subject_dn(self) -> str:
    """Build the subject distinguished name"""
```

**Returns:** `"CN=Name, OU=Unit, O=Org, L=City, ST=State, C=VN"`

##### `get_certificate_chain()`

```python
def get_certificate_chain(self) -> list:
    """Get certificate chain from this CA to root"""
```

**Returns:** List of CA instances from current to root

#### Meta Options

```python
class Meta:
    verbose_name = "Certificate Authority"
    verbose_name_plural = "Certificate Authorities"
    ordering = ['ca_type', 'name']
    indexes = [
        models.Index(fields=['ca_type', 'is_active']),
        models.Index(fields=['serial_number']),
    ]
```

---

## 2. Certificate Request Model (`certificate.py`)

### Class: `CertificateRequest`

Represents a Certificate Signing Request from a user.

```python
class CertificateRequest(models.Model):
    """
    Certificate Signing Request (CSR) from users.
    
    Users submit a CSR which is reviewed and approved by administrators
    before a certificate is issued.
    """
```

#### Choice Fields

```python
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
```

#### Fields

**Identity Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Primary key |
| `user` | ForeignKey(User) | Requesting user |

**Request Details:**

| Field | Type | Description |
|-------|------|-------------|
| `cert_type` | CharField(20) | Certificate type |
| `common_name` | CharField(255) | Requested CN |
| `organization` | CharField(255) | Organization |
| `organizational_unit` | CharField(255) | OU |

**Officer-specific Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `employee_id` | CharField(50) | Employee ID |
| `department` | CharField(255) | Department |
| `position` | CharField(255) | Job position |

**Citizen-specific Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `citizen_id` | CharField(20) | CMND/CCCD number |

**CSR Data:**

| Field | Type | Description |
|-------|------|-------------|
| `csr_pem` | TextField | PKCS#10 CSR (PEM) |
| `include_pq` | BooleanField | Include PQ key |
| `pq_public_key` | BinaryField | User's PQ public key |

**Status Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | CharField(20) | Request status |
| `reviewed_by` | ForeignKey(User) | Reviewer |
| `reviewed_at` | DateTimeField | Review time |
| `rejection_reason` | TextField | Rejection reason |

**Result:**

| Field | Type | Description |
|-------|------|-------------|
| `issued_certificate` | OneToOneField | Issued certificate |
| `requested_validity_days` | IntegerField | Requested validity |

#### Methods

##### `approve(reviewer)`

```python
def approve(self, reviewer):
    """Approve the certificate request"""
    self.status = 'APPROVED'
    self.reviewed_by = reviewer
    self.reviewed_at = timezone.now()
    self.save()
```

##### `reject(reviewer, reason)`

```python
def reject(self, reviewer, reason):
    """Reject the certificate request"""
    self.status = 'REJECTED'
    self.reviewed_by = reviewer
    self.reviewed_at = timezone.now()
    self.rejection_reason = reason
    self.save()
```

---

## 3. User Certificate Model (`certificate.py`)

### Class: `UserCertificate`

Represents a digital certificate issued to a user.

```python
class UserCertificate(models.Model):
    """
    Digital certificate issued to a user.
    
    Supports hybrid certificates with both classical (RSA/ECDSA) 
    and post-quantum (Dilithium) signatures.
    """
```

#### Choice Fields

```python
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
```

#### Fields

**Identity Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Primary key |
| `user` | ForeignKey(User) | Certificate owner |
| `issuing_ca` | ForeignKey(CA) | Issuing CA |

**Certificate Details:**

| Field | Type | Description |
|-------|------|-------------|
| `cert_type` | CharField(20) | Certificate type |
| `status` | CharField(20) | Certificate status |
| `serial_number` | CharField(64) | Unique serial |
| `subject_dn` | CharField(500) | Subject DN |

**Classical Cryptography:**

| Field | Type | Description |
|-------|------|-------------|
| `key_algorithm` | CharField(20) | Key algorithm |
| `certificate_pem` | TextField | X.509 certificate |
| `public_key_pem` | TextField | Public key |

**Post-Quantum Components:**

| Field | Type | Description |
|-------|------|-------------|
| `has_pq_key` | BooleanField | Has PQ key |
| `pq_algorithm` | CharField(30) | PQ algorithm |
| `pq_public_key` | BinaryField | PQ public key |
| `pq_certificate_extension` | TextField | PQ extension data |
| `hybrid_signature` | BinaryField | Combined signature |

**Validity:**

| Field | Type | Description |
|-------|------|-------------|
| `valid_from` | DateTimeField | Not before |
| `valid_until` | DateTimeField | Not after |

**Fingerprints:**

| Field | Type | Description |
|-------|------|-------------|
| `fingerprint_sha256` | CharField(64) | SHA-256 fingerprint |
| `fingerprint_sha1` | CharField(40) | SHA-1 fingerprint |

**Key Usage:**

| Field | Type | Description |
|-------|------|-------------|
| `key_usage` | JSONField | Key usage flags |
| `extended_key_usage` | JSONField | EKU OIDs |

**Revocation:**

| Field | Type | Description |
|-------|------|-------------|
| `revoked_at` | DateTimeField | Revocation time |
| `revocation_reason` | CharField(50) | Revocation reason |
| `revoked_by` | ForeignKey(User) | Revoking user |

**Usage Tracking:**

| Field | Type | Description |
|-------|------|-------------|
| `last_used_at` | DateTimeField | Last usage time |
| `usage_count` | IntegerField | Usage count |

#### Methods

##### `is_valid()`

```python
def is_valid(self) -> bool:
    """Check if certificate is currently valid"""
    now = timezone.now()
    return (
        self.status == 'ACTIVE' and
        self.valid_from <= now <= self.valid_until
    )
```

##### `is_expired()`

```python
def is_expired(self) -> bool:
    """Check if certificate has expired"""
    return timezone.now() > self.valid_until
```

##### `days_until_expiry()`

```python
def days_until_expiry(self) -> int:
    """Get number of days until certificate expires"""
    delta = self.valid_until - timezone.now()
    return max(0, delta.days)
```

##### `revoke(reason, revoked_by=None)`

```python
def revoke(self, reason, revoked_by=None):
    """Revoke the certificate"""
    self.status = 'REVOKED'
    self.revoked_at = timezone.now()
    self.revocation_reason = reason
    self.revoked_by = revoked_by
    self.save()
```

##### `record_usage()`

```python
def record_usage(self):
    """Record certificate usage"""
    self.last_used_at = timezone.now()
    self.usage_count += 1
    self.save(update_fields=['last_used_at', 'usage_count'])
```

##### `get_certificate_chain_pem()`

```python
def get_certificate_chain_pem(self) -> str:
    """Get full certificate chain in PEM format"""
    chain = [self.certificate_pem]
    current_ca = self.issuing_ca
    while current_ca:
        chain.append(current_ca.certificate_pem)
        current_ca = current_ca.parent_ca
    return '\n'.join(chain)
```

##### `can_sign_documents()`

```python
def can_sign_documents(self) -> bool:
    """Check if certificate can be used for document signing"""
    return (
        self.is_valid() and
        'digitalSignature' in self.key_usage
    )
```

##### `can_authenticate()`

```python
def can_authenticate(self) -> bool:
    """Check if certificate can be used for authentication"""
    return (
        self.is_valid() and
        ('clientAuth' in self.extended_key_usage or
         'digitalSignature' in self.key_usage)
    )
```

#### Meta Options

```python
class Meta:
    verbose_name = "User Certificate"
    verbose_name_plural = "User Certificates"
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['user', 'status']),
        models.Index(fields=['serial_number']),
        models.Index(fields=['fingerprint_sha256']),
    ]
```

---

## 4. Revocation Models (`revocation.py`)

### Class: `CertificateRevocationList`

Represents an X.509 CRL.

```python
class CertificateRevocationList(models.Model):
    """
    X.509 Certificate Revocation List (CRL).
    
    CRLs are periodically generated by CAs to list all revoked certificates.
    """
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Primary key |
| `issuing_ca` | ForeignKey(CA) | Issuing CA |
| `crl_number` | IntegerField | CRL sequence number |
| `this_update` | DateTimeField | Issuance time |
| `next_update` | DateTimeField | Next expected CRL |
| `crl_pem` | TextField | CRL in PEM format |
| `crl_der` | BinaryField | CRL in DER format |
| `signature_algorithm` | CharField(50) | Signature algorithm |
| `entries_count` | IntegerField | Number of entries |
| `created_at` | DateTimeField | Creation time |

#### Methods

##### `is_current()`

```python
def is_current(self) -> bool:
    """Check if this CRL is still current"""
    return timezone.now() < self.next_update
```

---

### Class: `RevokedCertificate`

Represents an entry in a CRL.

```python
class RevokedCertificate(models.Model):
    """
    Individual entry in a CRL representing a revoked certificate.
    """
```

#### Choice Fields

```python
REVOCATION_REASONS = [
    ('UNSPECIFIED', 'Unspecified'),
    ('KEY_COMPROMISE', 'Key Compromise'),
    ('CA_COMPROMISE', 'CA Compromise'),
    ('AFFILIATION_CHANGED', 'Affiliation Changed'),
    ('SUPERSEDED', 'Superseded'),
    ('CESSATION_OF_OPERATION', 'Cessation of Operation'),
    ('CERTIFICATE_HOLD', 'Certificate Hold'),
    ('REMOVE_FROM_CRL', 'Remove from CRL'),
    ('PRIVILEGE_WITHDRAWN', 'Privilege Withdrawn'),
    ('AA_COMPROMISE', 'AA Compromise'),
]
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Primary key |
| `certificate` | OneToOneField | Revoked certificate |
| `serial_number` | CharField(64) | Certificate serial |
| `revocation_date` | DateTimeField | Revocation time |
| `reason` | CharField(30) | Revocation reason |
| `invalidity_date` | DateTimeField | Key invalidity date |
| `first_included_in_crl` | ForeignKey(CRL) | First CRL inclusion |
| `created_at` | DateTimeField | Creation time |

---

### Class: `OCSPResponse`

Cached OCSP responses for performance.

```python
class OCSPResponse(models.Model):
    """
    Cached OCSP (Online Certificate Status Protocol) responses.
    """
```

#### Choice Fields

```python
CERT_STATUS = [
    ('GOOD', 'Good'),
    ('REVOKED', 'Revoked'),
    ('UNKNOWN', 'Unknown'),
]
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Primary key |
| `certificate_serial` | CharField(64) | Certificate serial |
| `issuer_name_hash` | CharField(64) | Issuer name hash |
| `issuer_key_hash` | CharField(64) | Issuer key hash |
| `status` | CharField(10) | Certificate status |
| `this_update` | DateTimeField | Response time |
| `next_update` | DateTimeField | Expected refresh |
| `revocation_time` | DateTimeField | Revocation time |
| `revocation_reason` | CharField(30) | Revocation reason |
| `response_der` | BinaryField | Full OCSP response |
| `created_at` | DateTimeField | Creation time |

---

## 5. Audit Model (`audit.py`)

### Class: `PKIAuditLog`

Comprehensive audit logging for PKI operations.

```python
class PKIAuditLog(models.Model):
    """
    Audit log for PKI operations.
    
    Records all significant events for compliance and security monitoring.
    """
```

#### Choice Fields

```python
EVENT_TYPES = [
    ('CA_CREATED', 'CA Created'),
    ('CA_DEACTIVATED', 'CA Deactivated'),
    ('CA_COMPROMISED', 'CA Compromised'),
    ('CERT_REQUESTED', 'Certificate Requested'),
    ('CERT_REQUEST_APPROVED', 'Request Approved'),
    ('CERT_REQUEST_REJECTED', 'Request Rejected'),
    ('CERT_ISSUED', 'Certificate Issued'),
    ('CERT_REVOKED', 'Certificate Revoked'),
    ('CERT_AUTH_SUCCESS', 'Certificate Auth Success'),
    ('CERT_AUTH_FAILURE', 'Certificate Auth Failure'),
    ('CRL_GENERATED', 'CRL Generated'),
    ('DOCUMENT_SIGNED', 'Document Signed'),
    ('SIGNATURE_VERIFIED', 'Signature Verified'),
    ('SIGNATURE_INVALID', 'Signature Invalid'),
    ('SYSTEM_ERROR', 'System Error'),
]

SEVERITY_LEVELS = [
    ('DEBUG', 'Debug'),
    ('INFO', 'Info'),
    ('WARNING', 'Warning'),
    ('ERROR', 'Error'),
    ('CRITICAL', 'Critical'),
]
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUIDField | Primary key |
| `timestamp` | DateTimeField | Event time |
| `event_type` | CharField(30) | Event type |
| `description` | TextField | Event description |
| `user` | ForeignKey(User) | Acting user |
| `ip_address` | GenericIPAddressField | Client IP |
| `user_agent` | CharField(500) | Browser/client info |
| `ca` | ForeignKey(CA) | Related CA |
| `certificate` | ForeignKey(Cert) | Related certificate |
| `severity` | CharField(10) | Severity level |
| `success` | BooleanField | Operation success |
| `error_message` | TextField | Error details |
| `details` | JSONField | Additional data |

#### Class Methods

##### `log()`

```python
@classmethod
def log(cls, event_type, description, user=None, request=None,
        ca=None, certificate=None, severity='INFO',
        success=True, error_message='', details=None):
    """Create an audit log entry"""
```

**Usage:**
```python
PKIAuditLog.log(
    event_type='CERT_ISSUED',
    description=f"Certificate issued to {user.email}",
    user=issuer,
    request=http_request,
    certificate=user_cert,
    severity='INFO',
    details={'serial': cert.serial_number}
)
```

---

## 6. Model Relationships Diagram

```
                    ┌─────────────────────┐
                    │        User         │
                    │  (authentication)   │
                    └─────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│CertificateRequest│  │ UserCertificate │  │  PKIAuditLog   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
           │                  │                  │
           └──────────┬───────┘                  │
                      │                          │
                      ▼                          │
         ┌─────────────────────┐                 │
         │ CertificateAuthority │◄───────────────┘
         └─────────────────────┘
                      │
           ┌──────────┴──────────┐
           │                     │
           ▼                     ▼
┌─────────────────┐    ┌─────────────────┐
│       CRL       │    │ RevokedCertificate│
└─────────────────┘    └─────────────────┘
```

---

## 7. Database Indexes

```python
# CertificateAuthority
models.Index(fields=['ca_type', 'is_active'])
models.Index(fields=['serial_number'])

# UserCertificate
models.Index(fields=['user', 'status'])
models.Index(fields=['serial_number'])
models.Index(fields=['fingerprint_sha256'])

# CertificateRequest
models.Index(fields=['user', 'status'])
models.Index(fields=['cert_type', 'status'])

# OCSPResponse
models.Index(fields=['certificate_serial', 'issuer_key_hash'])

# PKIAuditLog
models.Index(fields=['event_type', 'timestamp'])
models.Index(fields=['user', 'timestamp'])
```
