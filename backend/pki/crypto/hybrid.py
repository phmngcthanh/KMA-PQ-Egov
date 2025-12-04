"""
Hybrid Cryptography Module

Combines classical (RSA/ECDSA) and post-quantum (Dilithium) cryptography
for defense-in-depth security approach.

Hybrid Strategy:
- Signatures: Sign with both classical AND post-quantum algorithms
- Verification: Both signatures must be valid
- This ensures security even if one algorithm is broken
"""

import json
import base64
import hashlib
from typing import Tuple, Optional
from datetime import datetime

from .classical import ClassicalCrypto
from .post_quantum import PostQuantumCrypto


class HybridCrypto:
    """
    Hybrid cryptographic operations combining classical and post-quantum algorithms.
    
    This provides "quantum-safe" security by requiring both classical and
    post-quantum signatures to be valid. If quantum computers break classical
    crypto, the post-quantum signature remains secure. If a flaw is found
    in post-quantum algorithms, classical crypto provides backup.
    """
    
    # Hybrid algorithm configurations
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
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if hybrid crypto is available (requires both classical and PQ)."""
        return PostQuantumCrypto.is_available()
    
    @classmethod
    def generate_hybrid_keypair(cls, config: str = None) -> dict:
        """
        Generate a hybrid key pair (classical + post-quantum).
        
        Args:
            config: Hybrid configuration name
            
        Returns:
            dict: {
                'classical': {'private_key', 'public_key', 'algorithm'},
                'pq': {'private_key', 'public_key', 'algorithm'},
                'config': config_name
            }
        """
        config = config or cls.DEFAULT_CONFIG
        cfg = cls.HYBRID_CONFIGS.get(config)
        
        if not cfg:
            raise ValueError(f"Unknown hybrid config: {config}")
        
        # Generate classical key pair
        classical_private, classical_public = ClassicalCrypto.generate_keypair(
            cfg['classical']
        )
        
        # Generate post-quantum key pair
        pq_public, pq_private = PostQuantumCrypto.generate_signature_keypair(
            cfg['pq']
        )
        
        return {
            'classical': {
                'private_key': classical_private,
                'public_key': classical_public,
                'private_key_pem': ClassicalCrypto.serialize_private_key(classical_private),
                'public_key_pem': ClassicalCrypto.serialize_public_key(classical_public),
                'algorithm': cfg['classical'],
            },
            'pq': {
                'private_key': pq_private,
                'public_key': pq_public,
                'algorithm': cfg['pq'],
            },
            'config': config,
        }
    
    @classmethod
    def hybrid_sign(cls, message: bytes, 
                    classical_private_key,
                    pq_private_key: bytes,
                    config: str = None) -> dict:
        """
        Create a hybrid signature (classical + post-quantum).
        
        Args:
            message: Message to sign
            classical_private_key: Classical private key object
            pq_private_key: Post-quantum private key bytes
            config: Hybrid configuration
            
        Returns:
            dict: Hybrid signature structure
        """
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        config = config or cls.DEFAULT_CONFIG
        cfg = cls.HYBRID_CONFIGS.get(config, cls.HYBRID_CONFIGS[cls.DEFAULT_CONFIG])
        
        # Create message hash for consistent signing
        message_hash = hashlib.sha384(message).digest()
        
        # Classical signature
        classical_sig = ClassicalCrypto.sign_data(classical_private_key, message_hash)
        
        # Post-quantum signature
        pq_sig = PostQuantumCrypto.sign(pq_private_key, message_hash, cfg['pq'])
        
        # Combine into hybrid signature structure
        hybrid_signature = {
            'version': '1.0',
            'config': config,
            'timestamp': datetime.utcnow().isoformat(),
            'message_hash': base64.b64encode(message_hash).decode('ascii'),
            'classical_signature': base64.b64encode(classical_sig).decode('ascii'),
            'classical_algorithm': cfg['classical'],
            'pq_signature': base64.b64encode(pq_sig).decode('ascii'),
            'pq_algorithm': cfg['pq'],
        }
        
        return hybrid_signature
    
    @classmethod
    def hybrid_verify(cls, message: bytes,
                      hybrid_signature: dict,
                      classical_public_key,
                      pq_public_key: bytes) -> dict:
        """
        Verify a hybrid signature.
        
        Args:
            message: Original message
            hybrid_signature: Hybrid signature structure
            classical_public_key: Classical public key object
            pq_public_key: Post-quantum public key bytes
            
        Returns:
            dict: Verification result with details
        """
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        result = {
            'valid': False,
            'classical_valid': False,
            'pq_valid': False,
            'errors': [],
        }
        
        try:
            # Recalculate message hash
            message_hash = hashlib.sha384(message).digest()
            
            # Verify message hash matches (if included in signature)
            if 'message_hash' in hybrid_signature:
                expected_hash = base64.b64decode(hybrid_signature['message_hash'])
                if message_hash != expected_hash:
                    result['errors'].append("Message hash mismatch")
                    return result
            
            # Get configuration
            config = hybrid_signature.get('config', cls.DEFAULT_CONFIG)
            cfg = cls.HYBRID_CONFIGS.get(config, cls.HYBRID_CONFIGS[cls.DEFAULT_CONFIG])
            
            # Verify classical signature
            classical_sig = base64.b64decode(hybrid_signature['classical_signature'])
            result['classical_valid'] = ClassicalCrypto.verify_signature(
                classical_public_key, classical_sig, message_hash
            )
            if not result['classical_valid']:
                result['errors'].append("Classical signature invalid")
            
            # Verify post-quantum signature
            pq_sig = base64.b64decode(hybrid_signature['pq_signature'])
            result['pq_valid'] = PostQuantumCrypto.verify(
                pq_public_key, message_hash, pq_sig, cfg['pq']
            )
            if not result['pq_valid']:
                result['errors'].append("Post-quantum signature invalid")
            
            # Both must be valid for hybrid to be valid
            result['valid'] = result['classical_valid'] and result['pq_valid']
            
        except Exception as e:
            result['errors'].append(f"Verification error: {str(e)}")
        
        return result
    
    @classmethod
    def serialize_hybrid_signature(cls, hybrid_signature: dict) -> bytes:
        """
        Serialize hybrid signature to bytes for storage/transmission.
        
        Args:
            hybrid_signature: Hybrid signature dict
            
        Returns:
            bytes: JSON-encoded signature
        """
        return json.dumps(hybrid_signature, sort_keys=True).encode('utf-8')
    
    @classmethod
    def deserialize_hybrid_signature(cls, data: bytes) -> dict:
        """
        Deserialize hybrid signature from bytes.
        
        Args:
            data: JSON-encoded signature
            
        Returns:
            dict: Hybrid signature structure
        """
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
    
    @classmethod
    def create_hybrid_certificate_data(cls, 
                                        classical_cert_pem: bytes,
                                        pq_public_key: bytes,
                                        pq_algorithm: str,
                                        issuer_classical_key,
                                        issuer_pq_key: bytes) -> dict:
        """
        Create hybrid certificate data structure.
        
        This creates a structure that includes:
        - Classical X.509 certificate
        - Post-quantum public key and signature
        
        Args:
            classical_cert_pem: Traditional X.509 certificate
            pq_public_key: Post-quantum public key
            pq_algorithm: PQ algorithm used
            issuer_classical_key: Issuer's classical private key
            issuer_pq_key: Issuer's PQ private key
            
        Returns:
            dict: Hybrid certificate structure
        """
        if isinstance(classical_cert_pem, bytes):
            classical_cert_pem = classical_cert_pem.decode('utf-8')
        
        # Data to be signed with PQ
        cert_data = {
            'classical_certificate': classical_cert_pem,
            'pq_public_key': base64.b64encode(pq_public_key).decode('ascii'),
            'pq_algorithm': pq_algorithm,
        }
        
        data_to_sign = json.dumps(cert_data, sort_keys=True).encode('utf-8')
        
        # Create hybrid signature over the certificate data
        hybrid_sig = cls.hybrid_sign(
            data_to_sign,
            issuer_classical_key,
            issuer_pq_key
        )
        
        return {
            'version': '1.0',
            'type': 'hybrid_certificate',
            'classical_certificate': classical_cert_pem,
            'pq_public_key': base64.b64encode(pq_public_key).decode('ascii'),
            'pq_algorithm': pq_algorithm,
            'issuer_signature': hybrid_sig,
        }
    
    @classmethod
    def verify_hybrid_certificate(cls,
                                   hybrid_cert: dict,
                                   issuer_classical_public_key,
                                   issuer_pq_public_key: bytes) -> dict:
        """
        Verify a hybrid certificate.
        
        Args:
            hybrid_cert: Hybrid certificate structure
            issuer_classical_public_key: Issuer's classical public key
            issuer_pq_public_key: Issuer's PQ public key
            
        Returns:
            dict: Verification result
        """
        result = {
            'valid': False,
            'classical_cert_valid': False,
            'hybrid_signature_valid': False,
            'errors': [],
        }
        
        try:
            # Reconstruct signed data
            cert_data = {
                'classical_certificate': hybrid_cert['classical_certificate'],
                'pq_public_key': hybrid_cert['pq_public_key'],
                'pq_algorithm': hybrid_cert['pq_algorithm'],
            }
            data_to_verify = json.dumps(cert_data, sort_keys=True).encode('utf-8')
            
            # Verify hybrid signature
            sig_result = cls.hybrid_verify(
                data_to_verify,
                hybrid_cert['issuer_signature'],
                issuer_classical_public_key,
                issuer_pq_public_key
            )
            
            result['hybrid_signature_valid'] = sig_result['valid']
            result['classical_valid'] = sig_result['classical_valid']
            result['pq_valid'] = sig_result['pq_valid']
            result['errors'].extend(sig_result.get('errors', []))
            
            # Verify classical certificate (basic validation)
            try:
                cert = ClassicalCrypto.load_certificate(
                    hybrid_cert['classical_certificate']
                )
                result['classical_cert_valid'] = True
            except Exception as e:
                result['errors'].append(f"Classical certificate invalid: {e}")
            
            result['valid'] = (
                result['hybrid_signature_valid'] and 
                result['classical_cert_valid']
            )
            
        except Exception as e:
            result['errors'].append(f"Verification error: {str(e)}")
        
        return result
    
    @classmethod
    def get_fingerprint(cls, classical_public_key, pq_public_key: bytes) -> str:
        """
        Calculate combined fingerprint of hybrid key pair.
        
        Args:
            classical_public_key: Classical public key object
            pq_public_key: Post-quantum public key bytes
            
        Returns:
            str: Combined fingerprint (SHA-256)
        """
        classical_bytes = ClassicalCrypto.serialize_public_key(classical_public_key)
        combined = classical_bytes + pq_public_key
        return hashlib.sha256(combined).hexdigest().upper()
