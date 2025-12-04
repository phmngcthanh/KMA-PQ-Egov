# Code Analysis: PKI Services Module
## E-Government PKI System - NT208

**Module:** `backend/pki/services/`  
**Version:** 1.0  
**Date:** December 4, 2025

---

## Overview

The services module provides high-level business logic for PKI operations, abstracting the complexity of cryptographic operations and database management.

### Module Structure

```
backend/pki/services/
├── __init__.py          # Module exports
├── ca_service.py        # Certificate Authority operations
├── cert_service.py      # User certificate operations
└── pdf_service.py       # PDF signing and verification
```

---

## 1. Certificate Authority Service (`ca_service.py`)

### Class: `CAService`

Provides operations for Certificate Authority management including creation, CRL generation, and lifecycle management.

#### Constants

```python
ROOT_CA_VALIDITY_YEARS = 20
INTERMEDIATE_CA_VALIDITY_YEARS = 10
```

---

### Function: `get_master_key`

```python
@classmethod
def get_master_key(cls) -> bytes
```

**Purpose:** Retrieve the master encryption key for CA private keys.

**Returns:** `bytes` - 32-byte master key

**Security Note:** The master key should be stored securely (HSM, environment variable, or key vault).

**Implementation:**
```python
@classmethod
def get_master_key(cls) -> bytes:
    key = getattr(settings, 'PKI_MASTER_KEY', None)
    if not key:
        raise ValueError("PKI_MASTER_KEY not configured")
    return base64.b64decode(key)
```

---

### Function: `create_root_ca`

```python
@classmethod
def create_root_ca(cls,
                   name: str,
                   common_name: str,
                   organization: str = "E-Government PKI",
                   country: str = "VN",
                   organizational_unit: str = "",
                   locality: str = "",
                   state: str = "",
                   email: str = "",
                   key_algorithm: str = "RSA_4096",
                   pq_algorithm: str = "DILITHIUM3",
                   validity_years: int = None,
                   user=None,
                   request=None) -> CertificateAuthority
```

**Purpose:** Create a new Root Certificate Authority.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | Required | Unique CA name |
| `common_name` | str | Required | CN for certificate |
| `organization` | str | `"E-Government PKI"` | Organization name |
| `country` | str | `"VN"` | Country code |
| `organizational_unit` | str | `""` | OU name |
| `locality` | str | `""` | City |
| `state` | str | `""` | State/Province |
| `email` | str | `""` | Contact email |
| `key_algorithm` | str | `"RSA_4096"` | Classical algorithm |
| `pq_algorithm` | str | `"DILITHIUM3"` | Post-quantum algorithm |
| `validity_years` | int | `20` | Certificate validity |
| `user` | User | `None` | Creating user (audit) |
| `request` | Request | `None` | HTTP request (audit) |

**Returns:** `CertificateAuthority` - Created CA instance

**Process Flow:**
1. Generate classical key pair (RSA/ECDSA)
2. Generate post-quantum key pair (Dilithium)
3. Build subject distinguished name
4. Create self-signed X.509 certificate
5. Encrypt private keys with master key
6. Store in database
7. Create audit log entry

**Example:**
```python
root_ca = CAService.create_root_ca(
    name="E-Gov Root CA",
    common_name="E-Government Root Certificate Authority",
    organization="Ministry of Information",
    country="VN",
    key_algorithm="RSA_4096",
    pq_algorithm="DILITHIUM3",
    validity_years=20,
    user=request.user,
    request=request
)
```

**Database Record Created:**
```python
CertificateAuthority(
    name="E-Gov Root CA",
    common_name="E-Government Root Certificate Authority",
    ca_type="ROOT",
    parent_ca=None,
    path_length=2,
    key_algorithm="RSA_4096",
    certificate_pem="-----BEGIN CERTIFICATE-----...",
    private_key_pem_encrypted=b"<encrypted>",
    pq_algorithm="DILITHIUM3",
    pq_public_key=b"<dilithium-public-key>",
    pq_private_key_encrypted=b"<encrypted>",
    is_active=True,
    ...
)
```

---

### Function: `create_intermediate_ca`

```python
@classmethod
def create_intermediate_ca(cls,
                           name: str,
                           common_name: str,
                           parent_ca: CertificateAuthority,
                           ca_type: str,
                           organization: str = None,
                           country: str = None,
                           organizational_unit: str = "",
                           key_algorithm: str = None,
                           pq_algorithm: str = None,
                           validity_years: int = None,
                           user=None,
                           request=None) -> CertificateAuthority
```

**Purpose:** Create an Intermediate Certificate Authority under a parent CA.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | Required | Unique CA name |
| `common_name` | str | Required | CN for certificate |
| `parent_ca` | CertificateAuthority | Required | Parent CA |
| `ca_type` | str | Required | Type of intermediate CA |
| `organization` | str | Inherited | Organization (from parent) |
| `country` | str | Inherited | Country (from parent) |
| `key_algorithm` | str | Inherited | Classical algorithm |
| `pq_algorithm` | str | Inherited | PQ algorithm |
| `validity_years` | int | `10` | Certificate validity |

**CA Types:**
| Type | Purpose |
|------|---------|
| `INTERMEDIATE_OFFICER` | Issue certificates to government officers |
| `INTERMEDIATE_CITIZEN` | Issue certificates to citizens |
| `INTERMEDIATE_SERVICE` | Issue certificates for services/systems |

**Returns:** `CertificateAuthority` - Created intermediate CA

**Process Flow:**
1. Validate parent CA is active
2. Inherit settings from parent if not specified
3. Generate classical and PQ key pairs
4. Create CSR
5. Sign with parent CA's keys
6. Create hybrid signature (classical + PQ)
7. Store encrypted keys and certificate

**Example:**
```python
officer_ca = CAService.create_intermediate_ca(
    name="Officer Issuing CA",
    common_name="E-Government Officer Certificate Authority",
    parent_ca=root_ca,
    ca_type="INTERMEDIATE_OFFICER",
    user=request.user,
    request=request
)
```

---

### Function: `get_ca_for_cert_type`

```python
@classmethod
def get_ca_for_cert_type(cls, cert_type: str) -> Optional[CertificateAuthority]
```

**Purpose:** Get the appropriate CA for issuing a specific certificate type.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cert_type` | str | `'OFFICER'`, `'CITIZEN'`, or `'SERVICE'` |

**Returns:** `CertificateAuthority` or `None`

**Mapping:**
| Certificate Type | CA Type |
|-----------------|---------|
| `OFFICER` | `INTERMEDIATE_OFFICER` |
| `CITIZEN` | `INTERMEDIATE_CITIZEN` |
| `SERVICE` | `INTERMEDIATE_SERVICE` |

---

### Function: `generate_crl`

```python
@classmethod
def generate_crl(cls, ca: CertificateAuthority,
                 user=None, request=None) -> CertificateRevocationList
```

**Purpose:** Generate a new Certificate Revocation List for a CA.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ca` | CertificateAuthority | CA to generate CRL for |
| `user` | User | User generating CRL (audit) |
| `request` | Request | HTTP request (audit) |

**Returns:** `CertificateRevocationList` - Generated CRL

**CRL Contents:**
- Issuer name (from CA certificate)
- This update timestamp
- Next update timestamp (based on CA's CRL validity)
- List of revoked certificates with serial numbers and reasons
- CRL number (monotonically increasing)
- CA signature

**Process Flow:**
1. Query all revoked certificates issued by this CA
2. Build CRL using X.509 CRL builder
3. Add each revoked certificate entry
4. Sign CRL with CA's private key
5. Serialize to PEM and DER formats
6. Store CRL record in database
7. Update CA's last CRL number

**Example:**
```python
crl = CAService.generate_crl(
    ca=officer_ca,
    user=request.user,
    request=request
)
print(f"CRL #{crl.crl_number} generated with {crl.entries_count} entries")
```

---

### Function: `get_decrypted_private_key`

```python
@classmethod
def get_decrypted_private_key(cls, ca: CertificateAuthority)
```

**Purpose:** Decrypt and return CA's classical private key.

**Returns:** Private key object (RSA/ECDSA)

**Security:** Called only when signing operations are needed.

---

### Function: `get_decrypted_pq_private_key`

```python
@classmethod
def get_decrypted_pq_private_key(cls, ca: CertificateAuthority) -> bytes
```

**Purpose:** Decrypt and return CA's post-quantum private key.

**Returns:** `bytes` - Decrypted Dilithium private key

---

### Function: `deactivate_ca`

```python
@classmethod
def deactivate_ca(cls, ca: CertificateAuthority,
                  reason: str, user=None, request=None)
```

**Purpose:** Deactivate a Certificate Authority.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ca` | CertificateAuthority | CA to deactivate |
| `reason` | str | Reason for deactivation |

**Effects:**
- Sets `is_active = False`
- CA can no longer issue certificates
- Existing certificates remain valid
- Creates audit log entry

---

### Function: `mark_ca_compromised`

```python
@classmethod
def mark_ca_compromised(cls, ca: CertificateAuthority,
                        reason: str, user=None, request=None)
```

**Purpose:** Mark a CA as compromised (security incident).

**Effects:**
- Deactivates the CA
- Marks `is_compromised = True`
- All certificates issued by this CA should be re-validated
- Creates high-severity audit log entry

---

## 2. Certificate Service (`cert_service.py`)

### Class: `CertificateService`

Provides operations for end-entity certificate lifecycle management.

#### Constants

```python
CERT_VALIDITY = {
    'OFFICER': 730,   # 2 years
    'CITIZEN': 1095,  # 3 years
    'SERVICE': 365,   # 1 year
}
```

---

### Function: `create_certificate_request`

```python
@classmethod
def create_certificate_request(cls,
                                user,
                                cert_type: str,
                                common_name: str = None,
                                organization: str = "",
                                organizational_unit: str = "",
                                employee_id: str = "",
                                department: str = "",
                                position: str = "",
                                citizen_id: str = "",
                                include_pq: bool = True,
                                csr_pem: str = "",
                                pq_public_key: bytes = None,
                                validity_days: int = None,
                                request=None) -> CertificateRequest
```

**Purpose:** Create a new certificate signing request.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user` | User | Requesting user |
| `cert_type` | str | `'OFFICER'`, `'CITIZEN'`, `'SERVICE'` |
| `common_name` | str | Name on certificate (defaults to user's name) |
| `organization` | str | Organization name |
| `organizational_unit` | str | Department/Unit |
| `employee_id` | str | For OFFICER certificates |
| `department` | str | For OFFICER certificates |
| `position` | str | For OFFICER certificates |
| `citizen_id` | str | CMND/CCCD for CITIZEN certificates |
| `include_pq` | bool | Include post-quantum key |
| `csr_pem` | str | Client-generated PKCS#10 CSR |
| `pq_public_key` | bytes | Client's PQ public key |
| `validity_days` | int | Requested validity period |

**Returns:** `CertificateRequest` - Created request (status: PENDING)

**Example:**
```python
cert_request = CertificateService.create_certificate_request(
    user=citizen_user,
    cert_type='CITIZEN',
    common_name='Nguyen Van A',
    citizen_id='079123456789',
    include_pq=True,
)
```

---

### Function: `approve_request`

```python
@classmethod
def approve_request(cls, cert_request: CertificateRequest,
                    reviewer, request=None) -> CertificateRequest
```

**Purpose:** Approve a pending certificate request.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cert_request` | CertificateRequest | Request to approve |
| `reviewer` | User | Admin/Officer approving |

**Returns:** `CertificateRequest` - Updated request (status: APPROVED)

---

### Function: `reject_request`

```python
@classmethod
def reject_request(cls, cert_request: CertificateRequest,
                   reviewer, reason: str, request=None) -> CertificateRequest
```

**Purpose:** Reject a certificate request.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cert_request` | CertificateRequest | Request to reject |
| `reviewer` | User | Admin/Officer rejecting |
| `reason` | str | Rejection reason |

**Returns:** `CertificateRequest` - Updated request (status: REJECTED)

---

### Function: `issue_certificate`

```python
@classmethod
def issue_certificate(cls,
                      cert_request: CertificateRequest,
                      issuer=None,
                      request=None) -> UserCertificate
```

**Purpose:** Issue a certificate from an approved request.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `cert_request` | CertificateRequest | Approved request |
| `issuer` | User | Admin issuing certificate |

**Returns:** `UserCertificate` - Issued certificate

**Prerequisites:**
- Request must be in APPROVED status
- Appropriate intermediate CA must be active

**Process Flow:**
1. Validate request is approved
2. Get appropriate CA for certificate type
3. Decrypt CA private keys
4. Generate or use provided user keys
5. Build subject name from request data
6. Calculate validity period
7. Set key usage based on certificate type:
   - **OFFICER/CITIZEN:** digitalSignature, nonRepudiation, keyEncipherment
   - **SERVICE:** digitalSignature, keyEncipherment
8. Build and sign X.509 certificate
9. Generate hybrid signature if PQ enabled
10. Calculate fingerprints
11. Store certificate in database
12. Update request status to ISSUED
13. Increment CA's issued certificate count
14. Create audit log entry

**Certificate Extensions:**
```python
# Key Usage
digitalSignature=True
content_commitment=True  # nonRepudiation
key_encipherment=True

# Extended Key Usage (OFFICER/CITIZEN)
clientAuth
emailProtection
1.3.6.1.4.1.311.10.3.12  # documentSigning

# Extended Key Usage (SERVICE)
serverAuth
clientAuth
```

---

### Function: `quick_issue_certificate`

```python
@classmethod
def quick_issue_certificate(cls,
                            user,
                            cert_type: str,
                            issuer=None,
                            request=None,
                            **kwargs) -> Tuple[UserCertificate, bytes]
```

**Purpose:** Create and immediately issue a certificate (admin use).

**Returns:** `Tuple[UserCertificate, bytes]` - Certificate and private key (if generated server-side)

**Use Case:** Automated certificate issuance without manual approval.

---

### Function: `revoke_certificate`

```python
@classmethod
def revoke_certificate(cls,
                       certificate: UserCertificate,
                       reason: str,
                       revoker=None,
                       request=None) -> UserCertificate
```

**Purpose:** Revoke an active certificate.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `certificate` | UserCertificate | Certificate to revoke |
| `reason` | str | Revocation reason |
| `revoker` | User | User performing revocation |

**Valid Reasons:**
- `UNSPECIFIED`
- `KEY_COMPROMISE`
- `CA_COMPROMISE`
- `AFFILIATION_CHANGED`
- `SUPERSEDED`
- `CESSATION_OF_OPERATION`
- `CERTIFICATE_HOLD`
- `PRIVILEGE_WITHDRAWN`

**Returns:** `UserCertificate` - Updated certificate (status: REVOKED)

**Effects:**
1. Sets certificate status to REVOKED
2. Records revocation timestamp
3. Creates RevokedCertificate entry
4. Certificate will appear in next CRL

---

### Function: `verify_certificate`

```python
@classmethod
def verify_certificate(cls, certificate: UserCertificate) -> dict
```

**Purpose:** Verify a certificate's validity.

**Returns:**
```python
{
    'valid': True,              # Overall validity
    'status_valid': True,       # Status is ACTIVE
    'time_valid': True,         # Within validity period
    'ca_valid': True,           # Issuing CA is valid
    'signature_valid': True,    # Classical signature valid
    'pq_signature_valid': True, # PQ signature valid (if applicable)
    'errors': [],               # List of error messages
}
```

**Checks Performed:**
1. Certificate status is ACTIVE
2. Current time is within validity period
3. Issuing CA is active and valid
4. Classical signature is valid
5. Post-quantum signature is valid (if hybrid)

---

### Function: `get_user_certificates`

```python
@classmethod
def get_user_certificates(cls, user) -> list
```

**Purpose:** Get all certificates for a user.

**Returns:** `list[UserCertificate]` - User's certificates ordered by creation date

---

### Function: `get_active_certificate`

```python
@classmethod
def get_active_certificate(cls, user, cert_type: str = None) -> Optional[UserCertificate]
```

**Purpose:** Get user's active certificate, optionally filtered by type.

**Returns:** `UserCertificate` or `None`

---

### Function: `get_certificate_chain_pem`

```python
@classmethod
def get_certificate_chain_pem(cls, certificate: UserCertificate) -> str
```

**Purpose:** Get full certificate chain in PEM format.

**Returns:** `str` - Concatenated PEM certificates (user → intermediate → root)

---

## 3. PDF Signing Service (`pdf_service.py`)

### Class: `PDFSigningService`

Provides PDF signing and verification with hybrid signatures.

#### Constants

```python
SIGNATURE_WIDTH = 150
SIGNATURE_HEIGHT = 50
```

---

### Function: `is_available`

```python
@classmethod
def is_available(cls) -> bool
```

**Purpose:** Check if PDFNet is available for embedded signatures.

**Returns:** `bool` - True if PDFNetPython3 is installed

---

### Function: `sign_pdf`

```python
@classmethod
def sign_pdf(cls,
             input_file: str,
             certificate: UserCertificate,
             private_key_pem: bytes,
             pq_private_key: bytes = None,
             signature_id: str = None,
             x_coordinate: int = 100,
             y_coordinate: int = 100,
             page: int = 1,
             reason: str = "Document signed digitally",
             location: str = "Vietnam",
             output_file: str = None,
             signature_image: str = None,
             user=None,
             request=None) -> dict
```

**Purpose:** Sign a PDF document with user's certificate.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_file` | str | Required | Path to input PDF |
| `certificate` | UserCertificate | Required | Signing certificate |
| `private_key_pem` | bytes | Required | User's private key |
| `pq_private_key` | bytes | `None` | User's PQ private key |
| `signature_id` | str | Auto | Signature field ID |
| `x_coordinate` | int | `100` | X position |
| `y_coordinate` | int | `100` | Y position |
| `page` | int | `1` | Page number |
| `reason` | str | `"Document signed..."` | Signing reason |
| `location` | str | `"Vietnam"` | Signing location |
| `output_file` | str | Auto | Output path |
| `signature_image` | str | `None` | Signature image path |

**Returns:**
```python
{
    'success': True,
    'output_file': '/path/to/signed.pdf',
    'signature_id': 'sig_1701676800',
    'document_hash': '<sha384-hex>',
    'certificate_serial': 'ABC123...',
    'signer': 'CN=Nguyen Van A, O=...',
    'signed_at': '2025-12-04T10:00:00',
    'has_pq_signature': True,
    'pq_signature': '<base64>',
}
```

**Signing Methods:**
1. **Embedded (PDFNet available):** Signature embedded in PDF
2. **Detached (Fallback):** Separate `.sig` file created

---

### Function: `_sign_pdf_fallback`

```python
@classmethod
def _sign_pdf_fallback(cls, input_file, certificate, private_key_pem,
                       pq_private_key, output_file, user, request) -> dict
```

**Purpose:** Sign PDF with detached signature when PDFNet is unavailable.

**Creates:**
- Copy of original PDF
- `.sig` file containing:
  - Document hash (SHA-384)
  - Classical signature
  - PQ signature (if available)
  - Certificate information

**Signature File Format:**
```json
{
    "version": "1.0",
    "type": "detached_signature",
    "document_hash": "<base64-sha384>",
    "hash_algorithm": "SHA-384",
    "classical_signature": "<base64>",
    "classical_algorithm": "RSA_4096",
    "pq_signature": "<base64>",
    "pq_algorithm": "DILITHIUM3",
    "certificate_serial": "ABC123...",
    "certificate_subject": "CN=...",
    "certificate_pem": "-----BEGIN CERTIFICATE-----...",
    "signed_at": "2025-12-04T10:00:00"
}
```

---

### Function: `verify_pdf_signature`

```python
@classmethod
def verify_pdf_signature(cls,
                         pdf_file: str,
                         signature_file: str = None,
                         user=None,
                         request=None) -> dict
```

**Purpose:** Verify signatures on a PDF document.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `pdf_file` | str | Path to PDF file |
| `signature_file` | str | Path to .sig file (auto-detected) |

**Returns:**
```python
{
    'valid': True,
    'classical_valid': True,
    'pq_valid': True,
    'certificate_valid': True,
    'signer': 'CN=Nguyen Van A, O=...',
    'signed_at': '2025-12-04T10:00:00',
    'certificate_serial': 'ABC123...',
    'errors': [],
    'warnings': [],
}
```

**Verification Steps:**
1. Locate signature (embedded or detached)
2. Recalculate document hash
3. Compare hash with signed hash
4. Verify classical signature
5. Verify PQ signature (if present)
6. Check certificate validity period

---

### Function: `_verify_detached_signature`

```python
@classmethod
def _verify_detached_signature(cls, pdf_file: str, sig_file: str,
                                user=None, request=None) -> dict
```

**Purpose:** Verify a detached signature file.

**Process:**
1. Load signature data from `.sig` file
2. Read PDF content
3. Calculate SHA-384 hash
4. Compare with stored hash
5. Verify classical signature using certificate
6. Verify PQ signature if present

---

### Function: `_verify_embedded_signature`

```python
@classmethod
def _verify_embedded_signature(cls, pdf_file: str,
                                user=None, request=None) -> dict
```

**Purpose:** Verify embedded PDF signatures using PDFNet.

**Note:** Requires PDFNetPython3 library.

---

### Function: `get_signature_info`

```python
@classmethod
def get_signature_info(cls, pdf_file: str) -> dict
```

**Purpose:** Get information about signatures in a PDF.

**Returns:**
```python
{
    'has_signatures': True,
    'signatures': [
        {
            'type': 'detached',
            'signer': 'CN=Nguyen Van A',
            'signed_at': '2025-12-04T10:00:00',
            'has_pq': True,
        },
        {
            'type': 'embedded',
            'field_name': 'Signature1',
        }
    ]
}
```

---

## 4. Service Integration Examples

### Complete Certificate Issuance Flow

```python
from pki.services import CAService, CertificateService

# 1. Admin creates Root CA
root_ca = CAService.create_root_ca(
    name="E-Gov Root CA",
    common_name="E-Government Root Certificate Authority",
    user=admin_user
)

# 2. Admin creates Intermediate CA for citizens
citizen_ca = CAService.create_intermediate_ca(
    name="Citizen CA",
    common_name="E-Government Citizen CA",
    parent_ca=root_ca,
    ca_type="INTERMEDIATE_CITIZEN",
    user=admin_user
)

# 3. Citizen submits certificate request
cert_request = CertificateService.create_certificate_request(
    user=citizen_user,
    cert_type='CITIZEN',
    common_name='Nguyen Van A',
    citizen_id='079123456789'
)

# 4. Admin approves request
CertificateService.approve_request(cert_request, admin_user)

# 5. Certificate is issued
certificate = CertificateService.issue_certificate(cert_request, admin_user)

# 6. Citizen downloads certificate
chain = CertificateService.get_certificate_chain_pem(certificate)
```

### Document Signing Flow

```python
from pki.services import PDFSigningService, CertificateService

# 1. Get user's active certificate
certificate = CertificateService.get_active_certificate(user, 'CITIZEN')

# 2. Sign the document
result = PDFSigningService.sign_pdf(
    input_file='/path/to/document.pdf',
    certificate=certificate,
    private_key_pem=user_private_key,
    pq_private_key=user_pq_private_key,
    reason='Xác nhận hồ sơ',
    location='TP. Hồ Chí Minh'
)

# 3. Verify the signature
verification = PDFSigningService.verify_pdf_signature(result['output_file'])
print(f"Valid: {verification['valid']}")
```

### CRL Generation

```python
from pki.services import CAService

# Generate CRL for a CA
crl = CAService.generate_crl(citizen_ca, user=admin_user)
print(f"CRL #{crl.crl_number} contains {crl.entries_count} revoked certificates")

# CRL will include all certificates revoked by this CA
# Clients should download CRL periodically to check revocation status
```

---

## 5. Error Handling

All service methods raise exceptions for error conditions:

| Exception | Condition |
|-----------|-----------|
| `ValueError` | Invalid input parameters |
| `RuntimeError` | Cryptographic operation failed |
| `PermissionError` | Insufficient privileges |
| `ObjectDoesNotExist` | Required record not found |

**Example:**
```python
try:
    certificate = CertificateService.issue_certificate(request, issuer)
except ValueError as e:
    # Request not approved or invalid
    logger.error(f"Cannot issue certificate: {e}")
except RuntimeError as e:
    # Crypto operation failed
    logger.error(f"Signing failed: {e}")
```

---

## 6. Audit Logging

All service operations create audit log entries:

```python
PKIAuditLog.log(
    event_type='CERT_ISSUED',
    description=f"Certificate issued to {user.email}",
    user=issuer,
    request=http_request,
    ca=issuing_ca,
    certificate=user_cert,
    severity='INFO',
    details={
        'cert_type': 'CITIZEN',
        'serial_number': 'ABC123...',
        'has_pq': True,
    }
)
```

**Event Types:**
- `CA_CREATED`, `CA_DEACTIVATED`, `CA_COMPROMISED`
- `CERT_REQUESTED`, `CERT_REQUEST_APPROVED`, `CERT_REQUEST_REJECTED`
- `CERT_ISSUED`, `CERT_REVOKED`
- `CRL_GENERATED`
- `DOCUMENT_SIGNED`, `SIGNATURE_VERIFIED`, `SIGNATURE_INVALID`
