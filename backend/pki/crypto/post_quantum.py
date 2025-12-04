"""
Post-Quantum Cryptography Module

Provides post-quantum cryptographic operations using liboqs:
- Dilithium (ML-DSA) for digital signatures
- Kyber (ML-KEM) for key encapsulation (optional)

NIST Post-Quantum Cryptography Standards (2024):
- FIPS 204: ML-DSA (Module-Lattice-Based Digital Signature Algorithm) - formerly Dilithium
- FIPS 203: ML-KEM (Module-Lattice-Based Key Encapsulation Mechanism) - formerly Kyber
"""

import os
import base64
import hashlib
from typing import Tuple, Optional

# Try to import liboqs
try:
    import oqs
    OQS_AVAILABLE = True
except ImportError:
    OQS_AVAILABLE = False
    print("Warning: liboqs not available. Post-quantum features disabled.")


class PostQuantumCrypto:
    """
    Post-quantum cryptographic operations.
    
    Supports NIST standardized algorithms:
    - Dilithium2 (ML-DSA-44): NIST Level 2 security
    - Dilithium3 (ML-DSA-65): NIST Level 3 security (recommended)
    - Dilithium5 (ML-DSA-87): NIST Level 5 security
    - Falcon-512: Alternative signature scheme
    - Falcon-1024: Alternative with higher security
    - SPHINCS+-SHA2-128f: Hash-based signatures (stateless)
    """
    
    # Supported signature algorithms
    SIGNATURE_ALGORITHMS = {
        'DILITHIUM2': 'Dilithium2',
        'DILITHIUM3': 'Dilithium3',  # Recommended
        'DILITHIUM5': 'Dilithium5',
        'FALCON512': 'Falcon-512',
        'FALCON1024': 'Falcon-1024',
        'SPHINCS_SHA2_128F': 'SPHINCS+-SHA2-128f-simple',
    }
    
    # Supported KEM algorithms (for key exchange)
    KEM_ALGORITHMS = {
        'KYBER512': 'Kyber512',
        'KYBER768': 'Kyber768',  # Recommended
        'KYBER1024': 'Kyber1024',
    }
    
    # Default algorithm
    DEFAULT_SIG_ALGORITHM = 'DILITHIUM3'
    DEFAULT_KEM_ALGORITHM = 'KYBER768'
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if post-quantum cryptography is available."""
        return OQS_AVAILABLE
    
    @classmethod
    def get_oqs_version(cls) -> str:
        """Get liboqs version."""
        if not OQS_AVAILABLE:
            return "Not available"
        return oqs.oqs_version()
    
    @classmethod
    def list_available_algorithms(cls) -> dict:
        """List all available algorithms."""
        if not OQS_AVAILABLE:
            return {'signature': [], 'kem': []}
        
        return {
            'signature': oqs.get_enabled_sig_mechanisms(),
            'kem': oqs.get_enabled_kem_mechanisms(),
        }
    
    @classmethod
    def generate_signature_keypair(cls, algorithm: str = None) -> Tuple[bytes, bytes]:
        """
        Generate a post-quantum signature key pair.
        
        Args:
            algorithm: Signature algorithm name (default: DILITHIUM3)
            
        Returns:
            Tuple[bytes, bytes]: (public_key, private_key)
        """
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs is not available")
        
        algorithm = algorithm or cls.DEFAULT_SIG_ALGORITHM
        alg_name = cls.SIGNATURE_ALGORITHMS.get(algorithm, algorithm)
        
        with oqs.Signature(alg_name) as sig:
            public_key = sig.generate_keypair()
            private_key = sig.export_secret_key()
        
        return public_key, private_key
    
    @classmethod
    def sign(cls, private_key: bytes, message: bytes, 
             algorithm: str = None) -> bytes:
        """
        Create a post-quantum signature.
        
        Args:
            private_key: Private key bytes
            message: Message to sign
            algorithm: Signature algorithm (default: DILITHIUM3)
            
        Returns:
            bytes: Signature
        """
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs is not available")
        
        algorithm = algorithm or cls.DEFAULT_SIG_ALGORITHM
        alg_name = cls.SIGNATURE_ALGORITHMS.get(algorithm, algorithm)
        
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        with oqs.Signature(alg_name, private_key) as sig:
            signature = sig.sign(message)
        
        return signature
    
    @classmethod
    def verify(cls, public_key: bytes, message: bytes, signature: bytes,
               algorithm: str = None) -> bool:
        """
        Verify a post-quantum signature.
        
        Args:
            public_key: Public key bytes
            message: Original message
            signature: Signature to verify
            algorithm: Signature algorithm (default: DILITHIUM3)
            
        Returns:
            bool: True if signature is valid
        """
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs is not available")
        
        algorithm = algorithm or cls.DEFAULT_SIG_ALGORITHM
        alg_name = cls.SIGNATURE_ALGORITHMS.get(algorithm, algorithm)
        
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        with oqs.Signature(alg_name) as sig:
            return sig.verify(message, signature, public_key)
    
    @classmethod
    def generate_kem_keypair(cls, algorithm: str = None) -> Tuple[bytes, bytes]:
        """
        Generate a post-quantum KEM key pair.
        
        Args:
            algorithm: KEM algorithm name (default: KYBER768)
            
        Returns:
            Tuple[bytes, bytes]: (public_key, private_key)
        """
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs is not available")
        
        algorithm = algorithm or cls.DEFAULT_KEM_ALGORITHM
        alg_name = cls.KEM_ALGORITHMS.get(algorithm, algorithm)
        
        with oqs.KeyEncapsulation(alg_name) as kem:
            public_key = kem.generate_keypair()
            private_key = kem.export_secret_key()
        
        return public_key, private_key
    
    @classmethod
    def encapsulate(cls, public_key: bytes, 
                    algorithm: str = None) -> Tuple[bytes, bytes]:
        """
        Encapsulate a shared secret using KEM.
        
        Args:
            public_key: Recipient's public key
            algorithm: KEM algorithm (default: KYBER768)
            
        Returns:
            Tuple[bytes, bytes]: (ciphertext, shared_secret)
        """
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs is not available")
        
        algorithm = algorithm or cls.DEFAULT_KEM_ALGORITHM
        alg_name = cls.KEM_ALGORITHMS.get(algorithm, algorithm)
        
        with oqs.KeyEncapsulation(alg_name) as kem:
            ciphertext, shared_secret = kem.encap_secret(public_key)
        
        return ciphertext, shared_secret
    
    @classmethod
    def decapsulate(cls, private_key: bytes, ciphertext: bytes,
                    algorithm: str = None) -> bytes:
        """
        Decapsulate a shared secret using KEM.
        
        Args:
            private_key: Recipient's private key
            ciphertext: Ciphertext from encapsulation
            algorithm: KEM algorithm (default: KYBER768)
            
        Returns:
            bytes: Shared secret
        """
        if not OQS_AVAILABLE:
            raise RuntimeError("liboqs is not available")
        
        algorithm = algorithm or cls.DEFAULT_KEM_ALGORITHM
        alg_name = cls.KEM_ALGORITHMS.get(algorithm, algorithm)
        
        with oqs.KeyEncapsulation(alg_name, private_key) as kem:
            shared_secret = kem.decap_secret(ciphertext)
        
        return shared_secret
    
    @classmethod
    def get_algorithm_details(cls, algorithm: str) -> dict:
        """
        Get details about a specific algorithm.
        
        Args:
            algorithm: Algorithm name
            
        Returns:
            dict: Algorithm details
        """
        if not OQS_AVAILABLE:
            return {'error': 'liboqs not available'}
        
        # Check signature algorithms
        if algorithm in cls.SIGNATURE_ALGORITHMS:
            alg_name = cls.SIGNATURE_ALGORITHMS[algorithm]
            try:
                with oqs.Signature(alg_name) as sig:
                    return {
                        'type': 'signature',
                        'name': alg_name,
                        'internal_name': algorithm,
                        'public_key_length': sig.details['length_public_key'],
                        'secret_key_length': sig.details['length_secret_key'],
                        'signature_length': sig.details['length_signature'],
                        'nist_level': sig.details.get('claimed_nist_level', 'unknown'),
                    }
            except Exception as e:
                return {'error': str(e)}
        
        # Check KEM algorithms
        if algorithm in cls.KEM_ALGORITHMS:
            alg_name = cls.KEM_ALGORITHMS[algorithm]
            try:
                with oqs.KeyEncapsulation(alg_name) as kem:
                    return {
                        'type': 'kem',
                        'name': alg_name,
                        'internal_name': algorithm,
                        'public_key_length': kem.details['length_public_key'],
                        'secret_key_length': kem.details['length_secret_key'],
                        'ciphertext_length': kem.details['length_ciphertext'],
                        'shared_secret_length': kem.details['length_shared_secret'],
                        'nist_level': kem.details.get('claimed_nist_level', 'unknown'),
                    }
            except Exception as e:
                return {'error': str(e)}
        
        return {'error': f'Unknown algorithm: {algorithm}'}
    
    @classmethod
    def encode_public_key(cls, public_key: bytes) -> str:
        """
        Encode public key to base64 string.
        
        Args:
            public_key: Raw public key bytes
            
        Returns:
            str: Base64-encoded public key
        """
        return base64.b64encode(public_key).decode('ascii')
    
    @classmethod
    def decode_public_key(cls, encoded_key: str) -> bytes:
        """
        Decode base64 public key to bytes.
        
        Args:
            encoded_key: Base64-encoded public key
            
        Returns:
            bytes: Raw public key bytes
        """
        return base64.b64decode(encoded_key)
    
    @classmethod
    def get_public_key_fingerprint(cls, public_key: bytes) -> str:
        """
        Calculate SHA-256 fingerprint of public key.
        
        Args:
            public_key: Public key bytes
            
        Returns:
            str: Hex-encoded fingerprint
        """
        return hashlib.sha256(public_key).hexdigest().upper()
    
    @classmethod
    def create_pq_certificate_extension(cls, public_key: bytes, 
                                         algorithm: str = None) -> dict:
        """
        Create a post-quantum public key extension for X.509 certificate.
        
        This extension can be embedded in a traditional X.509 certificate
        to provide post-quantum security.
        
        Args:
            public_key: Post-quantum public key
            algorithm: Algorithm used
            
        Returns:
            dict: Extension data
        """
        algorithm = algorithm or cls.DEFAULT_SIG_ALGORITHM
        
        return {
            'oid': '1.3.6.1.4.1.99999.1.1',  # Example OID for PQ extension
            'algorithm': algorithm,
            'public_key': cls.encode_public_key(public_key),
            'fingerprint': cls.get_public_key_fingerprint(public_key),
        }


# Fallback implementation when liboqs is not available
class PostQuantumCryptoFallback:
    """
    Fallback implementation that raises clear errors when PQ crypto is unavailable.
    """
    
    @classmethod
    def is_available(cls) -> bool:
        return False
    
    @classmethod
    def generate_signature_keypair(cls, algorithm: str = None):
        raise NotImplementedError(
            "Post-quantum cryptography requires liboqs. "
            "Install with: pip install liboqs-python"
        )
    
    @classmethod
    def sign(cls, *args, **kwargs):
        raise NotImplementedError("liboqs not available")
    
    @classmethod
    def verify(cls, *args, **kwargs):
        raise NotImplementedError("liboqs not available")


# Export the appropriate class
if not OQS_AVAILABLE:
    # Override with fallback
    PostQuantumCrypto.is_available = lambda: False
