# Code Analysis: PKI Cryptography Module
## E-Government PKI System - NT208

**Module:** `backend/pki/crypto/`  
**Version:** 1.0  
**Date:** December 4, 2025

---

## Overview

The cryptography module provides all cryptographic operations for the PKI system, implementing a hybrid approach that combines classical cryptography (RSA/ECDSA) with post-quantum cryptography (Dilithium/Kyber).

### Module Structure

```
backend/pki/crypto/
├── __init__.py          # Module exports
├── classical.py         # Classical cryptography (RSA, ECDSA)
├── post_quantum.py      # Post-quantum cryptography (Dilithium, Kyber)
├── hybrid.py            # Hybrid cryptography combining both
└── utils.py             # Utility functions
```

---

## 1. Classical Cryptography (`classical.py`)

### Class: `ClassicalCrypto`

Main class providing traditional cryptographic operations using RSA and ECDSA algorithms.

#### Constants

```python
SUPPORTED_ALGORITHMS = ['RSA_2048', 'RSA_4096', 'ECDSA_P256', 'ECDSA_P384']
```

---

### Function: `generate_keypair`

```python
@classmethod
def generate_keypair(cls, algorithm: str = 'RSA_4096') -> Tuple[PrivateKey, PublicKey]
```

**Purpose:** Generate a classical cryptographic key pair.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `algorithm` | str | `'RSA_4096'` | Algorithm identifier |

**Supported Algorithms:**
- `RSA_2048`: RSA with 2048-bit key
- `RSA_4096`: RSA with 4096-bit key (recommended)
- `ECDSA_P256`: ECDSA with NIST P-256 curve
- `ECDSA_P384`: ECDSA with NIST P-384 curve

**Returns:** `Tuple[PrivateKey, PublicKey]` - Private and public key objects

**Example:**
```python
private_key, public_key = ClassicalCrypto.generate_keypair('RSA_4096')
```

---

### Function: `sign_data`

```python
@classmethod
def sign_data(cls, private_key, data: bytes) -> bytes
```

**Purpose:** Create a digital signature for data.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `private_key` | PrivateKey | RSA or ECDSA private key |
| `data` | bytes | Data to sign |

**Returns:** `bytes` - Digital signature

**Signature Algorithms Used:**
- RSA: PKCS#1 v1.5 with SHA-384
- ECDSA: ECDSA with SHA-384

**Example:**
```python
signature = ClassicalCrypto.sign_data(private_key, b"Hello World")
```

---

### Function: `verify_signature`

```python
@classmethod
def verify_signature(cls, public_key, signature: bytes, data: bytes) -> bool
```

**Purpose:** Verify a digital signature.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `public_key` | PublicKey | RSA or ECDSA public key |
| `signature` | bytes | Signature to verify |
| `data` | bytes | Original signed data |

**Returns:** `bool` - True if signature is valid

**Example:**
```python
is_valid = ClassicalCrypto.verify_signature(public_key, signature, data)
```

---

### Function: `build_subject_name`

```python
@classmethod
def build_subject_name(cls, common_name: str, organization: str = "",
                       organizational_unit: str = "", locality: str = "",
                       state: str = "", country: str = "VN",
                       email: str = "") -> x509.Name
```

**Purpose:** Build an X.509 subject distinguished name.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `common_name` | str | Required | CN - Common Name |
| `organization` | str | `""` | O - Organization |
| `organizational_unit` | str | `""` | OU - Organizational Unit |
| `locality` | str | `""` | L - Locality (City) |
| `state` | str | `""` | ST - State/Province |
| `country` | str | `"VN"` | C - Country Code |
| `email` | str | `""` | Email Address |

**Returns:** `x509.Name` - X.509 Name object

**Example:**
```python
subject = ClassicalCrypto.build_subject_name(
    common_name="Nguyen Van A",
    organization="E-Government",
    country="VN"
)
```

---

### Function: `create_ca_certificate`

```python
@classmethod
def create_ca_certificate(cls, private_key, public_key, subject_name,
                         is_root: bool = True, parent_cert=None, 
                         parent_key=None, validity_days: int = 3650,
                         path_length: int = None) -> x509.Certificate
```

**Purpose:** Create a Certificate Authority certificate.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `private_key` | PrivateKey | Required | CA's private key |
| `public_key` | PublicKey | Required | CA's public key |
| `subject_name` | x509.Name | Required | Subject distinguished name |
| `is_root` | bool | `True` | Is this a root CA? |
| `parent_cert` | Certificate | `None` | Parent CA certificate (for intermediate) |
| `parent_key` | PrivateKey | `None` | Parent CA private key (for signing) |
| `validity_days` | int | `3650` | Certificate validity period |
| `path_length` | int | `None` | Path length constraint |

**Returns:** `x509.Certificate` - CA certificate

**Certificate Extensions Added:**
- Basic Constraints: `CA=True, pathLength=<path_length>`
- Key Usage: `keyCertSign`, `cRLSign`, `digitalSignature`
- Subject Key Identifier
- Authority Key Identifier (for intermediate)

**Example:**
```python
# Root CA
root_cert = ClassicalCrypto.create_ca_certificate(
    private_key, public_key, subject,
    is_root=True, validity_days=7300, path_length=2
)

# Intermediate CA
intermediate_cert = ClassicalCrypto.create_ca_certificate(
    int_private_key, int_public_key, int_subject,
    is_root=False, parent_cert=root_cert, parent_key=root_private_key
)
```

---

### Function: `create_end_entity_certificate`

```python
@classmethod
def create_end_entity_certificate(cls, csr, issuer_cert, issuer_key,
                                   validity_days: int = 365,
                                   cert_type: str = 'CITIZEN') -> x509.Certificate
```

**Purpose:** Create an end-entity (user) certificate from a CSR.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csr` | CertificateSigningRequest | Required | PKCS#10 CSR |
| `issuer_cert` | Certificate | Required | Issuing CA certificate |
| `issuer_key` | PrivateKey | Required | Issuing CA private key |
| `validity_days` | int | `365` | Certificate validity |
| `cert_type` | str | `'CITIZEN'` | Certificate type |

**Certificate Types & Key Usage:**
| Type | Extended Key Usage |
|------|-------------------|
| `CITIZEN` | clientAuth, emailProtection, codeSigning |
| `OFFICER` | clientAuth, emailProtection, codeSigning |
| `SERVICE` | serverAuth, clientAuth |

**Returns:** `x509.Certificate` - User certificate

---

### Function: `load_certificate`

```python
@classmethod
def load_certificate(cls, pem_data: str) -> x509.Certificate
```

**Purpose:** Load a certificate from PEM format.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `pem_data` | str | PEM-encoded certificate |

**Returns:** `x509.Certificate` - Certificate object

---

### Function: `load_private_key`

```python
@classmethod
def load_private_key(cls, pem_data: bytes, password: bytes = None) -> PrivateKey
```

**Purpose:** Load a private key from PEM format.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `pem_data` | bytes | PEM-encoded private key |
| `password` | bytes | Decryption password (optional) |

**Returns:** `PrivateKey` - Private key object

---

### Function: `serialize_private_key`

```python
@classmethod
def serialize_private_key(cls, private_key, password: bytes = None) -> bytes
```

**Purpose:** Serialize a private key to PEM format.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `private_key` | PrivateKey | Private key object |
| `password` | bytes | Encryption password (optional) |

**Returns:** `bytes` - PEM-encoded private key

---

### Function: `serialize_public_key`

```python
@classmethod
def serialize_public_key(cls, public_key) -> bytes
```

**Purpose:** Serialize a public key to PEM format.

**Returns:** `bytes` - PEM-encoded public key

---

### Function: `get_certificate_fingerprint`

```python
@classmethod
def get_certificate_fingerprint(cls, certificate, algorithm: str = 'sha256') -> str
```

**Purpose:** Calculate certificate fingerprint.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `certificate` | Certificate | Required | X.509 certificate |
| `algorithm` | str | `'sha256'` | Hash algorithm |

**Returns:** `str` - Hex-encoded fingerprint (uppercase)

---

### Function: `encrypt_private_key`

```python
@classmethod
def encrypt_private_key(cls, private_key_pem: bytes, master_key: bytes) -> bytes
```

**Purpose:** Encrypt a private key using AES-256-GCM.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `private_key_pem` | bytes | PEM-encoded private key |
| `master_key` | bytes | 32-byte encryption key |

**Returns:** `bytes` - Encrypted private key (nonce + ciphertext + tag)

---

### Function: `decrypt_private_key`

```python
@classmethod
def decrypt_private_key(cls, encrypted_data: bytes, master_key: bytes) -> bytes
```

**Purpose:** Decrypt a private key.

**Returns:** `bytes` - Decrypted PEM-encoded private key

---

## 2. Post-Quantum Cryptography (`post_quantum.py`)

### Class: `PostQuantumCrypto`

Provides post-quantum cryptographic operations using NIST-standardized algorithms.

#### Constants

```python
SIGNATURE_ALGORITHMS = {
    'DILITHIUM2': 'Dilithium2',      # NIST Level 2
    'DILITHIUM3': 'Dilithium3',      # NIST Level 3 (Recommended)
    'DILITHIUM5': 'Dilithium5',      # NIST Level 5
    'FALCON512': 'Falcon-512',
    'FALCON1024': 'Falcon-1024',
    'SPHINCS_SHA2_128F': 'SPHINCS+-SHA2-128f-simple',
}

KEM_ALGORITHMS = {
    'KYBER512': 'Kyber512',
    'KYBER768': 'Kyber768',          # Recommended
    'KYBER1024': 'Kyber1024',
}

DEFAULT_SIG_ALGORITHM = 'DILITHIUM3'
DEFAULT_KEM_ALGORITHM = 'KYBER768'
```

---

### Function: `is_available`

```python
@classmethod
def is_available(cls) -> bool
```

**Purpose:** Check if liboqs is available for PQ operations.

**Returns:** `bool` - True if liboqs is installed

---

### Function: `get_oqs_version`

```python
@classmethod
def get_oqs_version(cls) -> str
```

**Purpose:** Get liboqs library version.

**Returns:** `str` - Version string or "Not available"

---

### Function: `list_available_algorithms`

```python
@classmethod
def list_available_algorithms(cls) -> dict
```

**Purpose:** List all available PQ algorithms.

**Returns:**
```python
{
    'signature': ['Dilithium2', 'Dilithium3', ...],
    'kem': ['Kyber512', 'Kyber768', ...]
}
```

---

### Function: `generate_signature_keypair`

```python
@classmethod
def generate_signature_keypair(cls, algorithm: str = None) -> Tuple[bytes, bytes]
```

**Purpose:** Generate a post-quantum signature key pair.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `algorithm` | str | `DILITHIUM3` | PQ signature algorithm |

**Returns:** `Tuple[bytes, bytes]` - (public_key, private_key)

**Key Sizes (Dilithium3):**
- Public Key: 1,952 bytes
- Private Key: 4,000 bytes
- Signature: 3,293 bytes

**Example:**
```python
public_key, private_key = PostQuantumCrypto.generate_signature_keypair('DILITHIUM3')
```

---

### Function: `sign`

```python
@classmethod
def sign(cls, private_key: bytes, message: bytes, 
         algorithm: str = None) -> bytes
```

**Purpose:** Create a post-quantum digital signature.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `private_key` | bytes | PQ private key |
| `message` | bytes | Message to sign |
| `algorithm` | str | PQ algorithm |

**Returns:** `bytes` - PQ signature

**Example:**
```python
signature = PostQuantumCrypto.sign(private_key, b"Document content", 'DILITHIUM3')
```

---

### Function: `verify`

```python
@classmethod
def verify(cls, public_key: bytes, message: bytes, signature: bytes,
           algorithm: str = None) -> bool
```

**Purpose:** Verify a post-quantum signature.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `public_key` | bytes | PQ public key |
| `message` | bytes | Original message |
| `signature` | bytes | Signature to verify |
| `algorithm` | str | PQ algorithm |

**Returns:** `bool` - True if valid

---

### Function: `generate_kem_keypair`

```python
@classmethod
def generate_kem_keypair(cls, algorithm: str = None) -> Tuple[bytes, bytes]
```

**Purpose:** Generate a Key Encapsulation Mechanism key pair.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `algorithm` | str | `KYBER768` | KEM algorithm |

**Returns:** `Tuple[bytes, bytes]` - (public_key, private_key)

---

### Function: `encapsulate`

```python
@classmethod
def encapsulate(cls, public_key: bytes, 
                algorithm: str = None) -> Tuple[bytes, bytes]
```

**Purpose:** Encapsulate a shared secret (sender side).

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `public_key` | bytes | Recipient's public key |
| `algorithm` | str | KEM algorithm |

**Returns:** `Tuple[bytes, bytes]` - (ciphertext, shared_secret)

**Example:**
```python
ciphertext, shared_secret = PostQuantumCrypto.encapsulate(recipient_public_key)
# Send ciphertext to recipient
```

---

### Function: `decapsulate`

```python
@classmethod
def decapsulate(cls, private_key: bytes, ciphertext: bytes,
                algorithm: str = None) -> bytes
```

**Purpose:** Decapsulate a shared secret (recipient side).

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `private_key` | bytes | Recipient's private key |
| `ciphertext` | bytes | Ciphertext from encapsulation |
| `algorithm` | str | KEM algorithm |

**Returns:** `bytes` - Shared secret

**Example:**
```python
shared_secret = PostQuantumCrypto.decapsulate(private_key, ciphertext)
# Use shared_secret for symmetric encryption
```

---

### Function: `get_algorithm_details`

```python
@classmethod
def get_algorithm_details(cls, algorithm: str) -> dict
```

**Purpose:** Get details about a specific algorithm.

**Returns:**
```python
{
    'type': 'signature',  # or 'kem'
    'name': 'Dilithium3',
    'internal_name': 'DILITHIUM3',
    'public_key_length': 1952,
    'secret_key_length': 4000,
    'signature_length': 3293,  # for signatures
    'nist_level': 3,
}
```

---

### Function: `encode_public_key`

```python
@classmethod
def encode_public_key(cls, public_key: bytes) -> str
```

**Purpose:** Base64 encode a public key.

**Returns:** `str` - Base64-encoded public key

---

### Function: `decode_public_key`

```python
@classmethod
def decode_public_key(cls, encoded_key: str) -> bytes
```

**Purpose:** Decode a Base64 public key.

**Returns:** `bytes` - Raw public key

---

### Function: `get_public_key_fingerprint`

```python
@classmethod
def get_public_key_fingerprint(cls, public_key: bytes) -> str
```

**Purpose:** Calculate SHA-256 fingerprint of PQ public key.

**Returns:** `str` - Hex-encoded fingerprint (uppercase)

---

### Function: `create_pq_certificate_extension`

```python
@classmethod
def create_pq_certificate_extension(cls, public_key: bytes, 
                                     algorithm: str = None) -> dict
```

**Purpose:** Create PQ extension data for X.509 certificate.

**Returns:**
```python
{
    'oid': '1.3.6.1.4.1.99999.1.1',
    'algorithm': 'DILITHIUM3',
    'public_key': '<base64-encoded>',
    'fingerprint': '<sha256-hex>',
}
```

---

## 3. Hybrid Cryptography (`hybrid.py`)

### Class: `HybridCrypto`

Combines classical and post-quantum cryptography for defense-in-depth security.

#### Constants

```python
HYBRID_CONFIGS = {
    'HYBRID_RSA4096_DILITHIUM3': {
        'classical': 'RSA_4096',
        'pq': 'DILITHIUM3',
        'description': 'RSA-4096 + Dilithium3 (Recommended)',
    },
    'HYBRID_ECDSA384_DILITHIUM3': {
        'classical': 'ECDSA_P384',
        'pq': 'DILITHIUM3',
        'description': 'ECDSA P-384 + Dilithium3',
    },
    'HYBRID_RSA4096_DILITHIUM5': {
        'classical': 'RSA_4096',
        'pq': 'DILITHIUM5',
        'description': 'RSA-4096 + Dilithium5 (Highest Security)',
    },
}

DEFAULT_CONFIG = 'HYBRID_RSA4096_DILITHIUM3'
```

---

### Function: `is_available`

```python
@classmethod
def is_available(cls) -> bool
```

**Purpose:** Check if hybrid crypto is available.

**Returns:** `bool` - True if both classical and PQ are available

---

### Function: `generate_hybrid_keypair`

```python
@classmethod
def generate_hybrid_keypair(cls, config: str = None) -> dict
```

**Purpose:** Generate a hybrid key pair (classical + PQ).

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | str | `HYBRID_RSA4096_DILITHIUM3` | Hybrid configuration |

**Returns:**
```python
{
    'classical': {
        'private_key': <PrivateKey>,
        'public_key': <PublicKey>,
        'private_key_pem': b'-----BEGIN PRIVATE KEY-----...',
        'public_key_pem': b'-----BEGIN PUBLIC KEY-----...',
        'algorithm': 'RSA_4096',
    },
    'pq': {
        'private_key': b'...',
        'public_key': b'...',
        'algorithm': 'DILITHIUM3',
    },
    'config': 'HYBRID_RSA4096_DILITHIUM3',
}
```

---

### Function: `hybrid_sign`

```python
@classmethod
def hybrid_sign(cls, message: bytes, 
                classical_private_key,
                pq_private_key: bytes,
                config: str = None) -> dict
```

**Purpose:** Create a hybrid signature (classical + PQ).

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | bytes | Message to sign |
| `classical_private_key` | PrivateKey | RSA/ECDSA private key |
| `pq_private_key` | bytes | Dilithium private key |
| `config` | str | Hybrid configuration |

**Returns:**
```python
{
    'version': '1.0',
    'config': 'HYBRID_RSA4096_DILITHIUM3',
    'timestamp': '2025-12-04T10:30:00',
    'message_hash': '<base64-sha384>',
    'classical_signature': '<base64>',
    'classical_algorithm': 'RSA_4096',
    'pq_signature': '<base64>',
    'pq_algorithm': 'DILITHIUM3',
}
```

**Signing Process:**
1. Calculate SHA-384 hash of message
2. Sign hash with classical algorithm
3. Sign hash with PQ algorithm
4. Combine into hybrid signature structure

---

### Function: `hybrid_verify`

```python
@classmethod
def hybrid_verify(cls, message: bytes,
                  hybrid_signature: dict,
                  classical_public_key,
                  pq_public_key: bytes) -> dict
```

**Purpose:** Verify a hybrid signature.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | bytes | Original message |
| `hybrid_signature` | dict | Hybrid signature structure |
| `classical_public_key` | PublicKey | RSA/ECDSA public key |
| `pq_public_key` | bytes | Dilithium public key |

**Returns:**
```python
{
    'valid': True,              # Overall validity
    'classical_valid': True,    # Classical signature valid
    'pq_valid': True,           # PQ signature valid
    'errors': [],               # List of error messages
}
```

**Verification Logic:**
- **Both signatures must be valid** for `valid=True`
- Defense-in-depth: if quantum computers break classical, PQ remains secure
- If flaw found in PQ, classical provides backup

---

### Function: `serialize_hybrid_signature`

```python
@classmethod
def serialize_hybrid_signature(cls, hybrid_signature: dict) -> bytes
```

**Purpose:** Serialize hybrid signature to JSON bytes.

**Returns:** `bytes` - JSON-encoded signature

---

### Function: `deserialize_hybrid_signature`

```python
@classmethod
def deserialize_hybrid_signature(cls, data: bytes) -> dict
```

**Purpose:** Deserialize hybrid signature from JSON.

**Returns:** `dict` - Hybrid signature structure

---

### Function: `create_hybrid_certificate_data`

```python
@classmethod
def create_hybrid_certificate_data(cls, 
                                    classical_cert_pem: bytes,
                                    pq_public_key: bytes,
                                    pq_algorithm: str,
                                    issuer_classical_key,
                                    issuer_pq_key: bytes) -> dict
```

**Purpose:** Create a hybrid certificate structure.

**Returns:**
```python
{
    'version': '1.0',
    'type': 'hybrid_certificate',
    'classical_certificate': '<PEM>',
    'pq_public_key': '<base64>',
    'pq_algorithm': 'DILITHIUM3',
    'issuer_signature': {<hybrid_signature>},
}
```

---

### Function: `verify_hybrid_certificate`

```python
@classmethod
def verify_hybrid_certificate(cls,
                               hybrid_cert: dict,
                               issuer_classical_public_key,
                               issuer_pq_public_key: bytes) -> dict
```

**Purpose:** Verify a hybrid certificate.

**Returns:**
```python
{
    'valid': True,
    'classical_cert_valid': True,
    'hybrid_signature_valid': True,
    'classical_valid': True,
    'pq_valid': True,
    'errors': [],
}
```

---

### Function: `get_fingerprint`

```python
@classmethod
def get_fingerprint(cls, classical_public_key, pq_public_key: bytes) -> str
```

**Purpose:** Calculate combined fingerprint of hybrid key pair.

**Returns:** `str` - SHA-256 hex fingerprint of concatenated keys

---

## 4. Utility Functions (`utils.py`)

### Class: `CryptoUtils`

Provides utility functions for cryptographic operations.

---

### Function: `build_dn`

```python
@classmethod
def build_dn(cls, cn: str = "", o: str = "", ou: str = "",
             c: str = "", email: str = "") -> str
```

**Purpose:** Build a distinguished name string.

**Returns:** `str` - DN string (e.g., "CN=John, O=Gov, C=VN")

---

### Function: `generate_random_bytes`

```python
@classmethod
def generate_random_bytes(cls, length: int) -> bytes
```

**Purpose:** Generate cryptographically secure random bytes.

**Returns:** `bytes` - Random bytes

---

### Function: `constant_time_compare`

```python
@classmethod
def constant_time_compare(cls, a: bytes, b: bytes) -> bool
```

**Purpose:** Compare two byte strings in constant time (prevents timing attacks).

**Returns:** `bool` - True if equal

---

## 5. Security Considerations

### Key Storage
- Private keys are encrypted using AES-256-GCM
- Master key should be stored in HSM or secure key vault
- Never log or expose private keys

### Algorithm Selection
- **Recommended Classical:** RSA-4096 or ECDSA P-384
- **Recommended PQ Signature:** Dilithium3 (ML-DSA-65)
- **Recommended KEM:** Kyber768 (ML-KEM-768)

### Hybrid Approach Benefits
1. **Quantum-safe:** PQ algorithms protect against future quantum attacks
2. **Backward compatible:** Classical algorithms work with current systems
3. **Defense-in-depth:** If one algorithm is broken, the other provides protection

### Performance Considerations
| Operation | RSA-4096 | Dilithium3 | Hybrid |
|-----------|----------|------------|--------|
| Key Gen | ~100ms | ~1ms | ~101ms |
| Sign | ~5ms | ~2ms | ~7ms |
| Verify | ~0.5ms | ~1ms | ~1.5ms |
| Signature Size | 512B | 3,293B | ~3.8KB |

---

## 6. Dependencies

```python
# Required
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

# Optional (for PQ)
import oqs  # liboqs-python
```

**Installation:**
```bash
pip install cryptography
pip install liboqs-python  # Requires liboqs C library
```
