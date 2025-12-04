"""
Cryptographic Utility Functions

Common utilities for PKI operations.
"""

import os
import secrets
import hashlib
import base64
from datetime import datetime
from typing import Optional


class CryptoUtils:
    """
    Utility functions for cryptographic operations.
    """
    
    # Key derivation settings
    MASTER_KEY_LENGTH = 32  # 256 bits
    SALT_LENGTH = 16
    
    @classmethod
    def generate_master_key(cls) -> bytes:
        """
        Generate a cryptographically secure master key.
        
        Returns:
            bytes: 32-byte random key
        """
        return secrets.token_bytes(cls.MASTER_KEY_LENGTH)
    
    @classmethod
    def generate_serial_number(cls) -> str:
        """
        Generate a unique certificate serial number.
        
        Returns:
            str: Hex-encoded serial number
        """
        # Combine timestamp with random bytes for uniqueness
        timestamp = int(datetime.utcnow().timestamp() * 1000000)
        random_bytes = secrets.token_bytes(8)
        
        combined = timestamp.to_bytes(8, 'big') + random_bytes
        return hashlib.sha256(combined).hexdigest()[:32].upper()
    
    @classmethod
    def generate_random_password(cls, length: int = 32) -> str:
        """
        Generate a random password.
        
        Args:
            length: Password length
            
        Returns:
            str: Random password
        """
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @classmethod
    def hash_data(cls, data: bytes, algorithm: str = 'sha256') -> str:
        """
        Hash data using specified algorithm.
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm (sha256, sha384, sha512, sha3_256)
            
        Returns:
            str: Hex-encoded hash
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithm == 'sha256':
            return hashlib.sha256(data).hexdigest()
        elif algorithm == 'sha384':
            return hashlib.sha384(data).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(data).hexdigest()
        elif algorithm == 'sha3_256':
            return hashlib.sha3_256(data).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    @classmethod
    def constant_time_compare(cls, a: bytes, b: bytes) -> bool:
        """
        Compare two byte strings in constant time.
        
        This prevents timing attacks.
        
        Args:
            a: First byte string
            b: Second byte string
            
        Returns:
            bool: True if equal
        """
        return secrets.compare_digest(a, b)
    
    @classmethod
    def encode_base64(cls, data: bytes) -> str:
        """
        Encode bytes to base64 string.
        
        Args:
            data: Bytes to encode
            
        Returns:
            str: Base64-encoded string
        """
        return base64.b64encode(data).decode('ascii')
    
    @classmethod
    def decode_base64(cls, data: str) -> bytes:
        """
        Decode base64 string to bytes.
        
        Args:
            data: Base64-encoded string
            
        Returns:
            bytes: Decoded bytes
        """
        return base64.b64decode(data)
    
    @classmethod
    def encode_base64url(cls, data: bytes) -> str:
        """
        Encode bytes to URL-safe base64 string.
        
        Args:
            data: Bytes to encode
            
        Returns:
            str: URL-safe base64-encoded string
        """
        return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')
    
    @classmethod
    def decode_base64url(cls, data: str) -> bytes:
        """
        Decode URL-safe base64 string to bytes.
        
        Args:
            data: URL-safe base64-encoded string
            
        Returns:
            bytes: Decoded bytes
        """
        # Add padding if necessary
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.urlsafe_b64decode(data)
    
    @classmethod
    def format_fingerprint(cls, fingerprint: str, separator: str = ':') -> str:
        """
        Format fingerprint with separators for readability.
        
        Args:
            fingerprint: Hex-encoded fingerprint
            separator: Separator character
            
        Returns:
            str: Formatted fingerprint (e.g., "AB:CD:EF:...")
        """
        return separator.join(
            fingerprint[i:i+2] for i in range(0, len(fingerprint), 2)
        )
    
    @classmethod
    def parse_dn(cls, dn_string: str) -> dict:
        """
        Parse a Distinguished Name string into components.
        
        Args:
            dn_string: DN string (e.g., "CN=John, O=Company, C=VN")
            
        Returns:
            dict: Parsed components
        """
        components = {}
        if not dn_string:
            return components
        
        # Split by comma, handling escaped commas
        parts = []
        current = ""
        escaped = False
        for char in dn_string:
            if char == '\\':
                escaped = True
                current += char
            elif char == ',' and not escaped:
                parts.append(current.strip())
                current = ""
            else:
                current += char
                escaped = False
        if current:
            parts.append(current.strip())
        
        # Parse each part
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                components[key.strip().upper()] = value.strip()
        
        return components
    
    @classmethod
    def build_dn(cls, cn: str = None, ou: str = None, o: str = None,
                 l: str = None, st: str = None, c: str = None,
                 email: str = None) -> str:
        """
        Build a Distinguished Name string.
        
        Args:
            cn: Common Name
            ou: Organizational Unit
            o: Organization
            l: Locality
            st: State/Province
            c: Country
            email: Email Address
            
        Returns:
            str: DN string
        """
        parts = []
        if cn:
            parts.append(f"CN={cn}")
        if ou:
            parts.append(f"OU={ou}")
        if o:
            parts.append(f"O={o}")
        if l:
            parts.append(f"L={l}")
        if st:
            parts.append(f"ST={st}")
        if c:
            parts.append(f"C={c}")
        if email:
            parts.append(f"emailAddress={email}")
        
        return ", ".join(parts)
    
    @classmethod
    def validate_certificate_validity(cls, not_before: datetime, 
                                       not_after: datetime) -> bool:
        """
        Check if current time is within certificate validity period.
        
        Args:
            not_before: Certificate not valid before
            not_after: Certificate not valid after
            
        Returns:
            bool: True if certificate is currently valid
        """
        now = datetime.utcnow()
        return not_before <= now <= not_after
    
    @classmethod
    def get_env_master_key(cls) -> Optional[bytes]:
        """
        Get master key from environment variable.
        
        The master key should be stored securely (HSM, key vault, etc.)
        For development, it can be in an environment variable.
        
        Returns:
            bytes: Master key or None
        """
        key_hex = os.environ.get('PKI_MASTER_KEY')
        if key_hex:
            return bytes.fromhex(key_hex)
        return None
    
    @classmethod
    def generate_and_save_master_key(cls, filepath: str) -> bytes:
        """
        Generate a master key and save to file.
        
        WARNING: Only for development. In production, use HSM or key vault.
        
        Args:
            filepath: Path to save the key
            
        Returns:
            bytes: Generated master key
        """
        key = cls.generate_master_key()
        
        # Save as hex for easier handling
        with open(filepath, 'w') as f:
            f.write(key.hex())
        
        # Set restrictive permissions
        os.chmod(filepath, 0o600)
        
        return key
    
    @classmethod
    def load_master_key(cls, filepath: str) -> bytes:
        """
        Load master key from file.
        
        Args:
            filepath: Path to key file
            
        Returns:
            bytes: Master key
        """
        with open(filepath, 'r') as f:
            key_hex = f.read().strip()
        return bytes.fromhex(key_hex)
