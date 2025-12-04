"""
Certificate Authentication Backend

Provides authentication using client X.509 certificates.
This enables login via smart cards, browser certificates, or mobile certificates.
"""

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import UserCertificate, PKIAuditLog
from ..crypto import ClassicalCrypto

User = get_user_model()


class CertificateAuthenticationBackend(BaseBackend):
    """
    Authentication backend that authenticates users via X.509 client certificates.
    
    This backend is used when the user presents a client certificate during
    TLS handshake. The web server (nginx/apache) extracts the certificate
    and passes it to Django via headers.
    
    Usage:
        1. Configure web server to request client certificates
        2. Pass certificate info via headers (e.g., X-SSL-CLIENT-CERT)
        3. Add this backend to AUTHENTICATION_BACKENDS
        4. Use CertificateLoginView for login
    """
    
    def authenticate(self, request, certificate_pem=None, 
                     certificate_fingerprint=None, **kwargs):
        """
        Authenticate a user based on their certificate.
        
        Args:
            request: HTTP request
            certificate_pem: Certificate in PEM format
            certificate_fingerprint: SHA-256 fingerprint of certificate
            
        Returns:
            User instance if authenticated, None otherwise
        """
        if not certificate_pem and not certificate_fingerprint:
            return None
        
        try:
            user_cert = None
            
            if certificate_fingerprint:
                # Find certificate by fingerprint
                user_cert = UserCertificate.objects.filter(
                    fingerprint_sha256__iexact=certificate_fingerprint.replace(':', ''),
                    status='ACTIVE'
                ).first()
            
            elif certificate_pem:
                # Parse certificate and find by fingerprint
                cert = ClassicalCrypto.load_certificate(certificate_pem)
                fingerprint = ClassicalCrypto.get_certificate_fingerprint(cert)
                
                user_cert = UserCertificate.objects.filter(
                    fingerprint_sha256=fingerprint,
                    status='ACTIVE'
                ).first()
            
            if not user_cert:
                self._log_auth_failure(
                    request, 
                    "Certificate not found or inactive",
                    certificate_fingerprint or "Unknown"
                )
                return None
            
            # Verify certificate is valid
            if not user_cert.is_valid():
                self._log_auth_failure(
                    request,
                    "Certificate expired or revoked",
                    user_cert.serial_number
                )
                return None
            
            # Check if certificate can authenticate
            if not user_cert.can_authenticate():
                self._log_auth_failure(
                    request,
                    "Certificate not authorized for authentication",
                    user_cert.serial_number
                )
                return None
            
            # Verify certificate chain (optional, depending on setup)
            # This is typically done by the web server during TLS handshake
            
            # Get the user
            user = user_cert.user
            
            if not user.is_active:
                self._log_auth_failure(
                    request,
                    "User account is inactive",
                    user_cert.serial_number
                )
                return None
            
            # Record successful authentication
            user_cert.record_usage()
            
            self._log_auth_success(request, user, user_cert)
            
            return user
            
        except Exception as e:
            self._log_auth_failure(
                request,
                f"Authentication error: {str(e)}",
                certificate_fingerprint or "Unknown"
            )
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID.
        
        Required by Django authentication backend.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def _log_auth_success(self, request, user, certificate):
        """Log successful certificate authentication."""
        PKIAuditLog.log(
            event_type='CERT_AUTH_SUCCESS',
            description=f"Certificate authentication successful for {user.email}",
            user=user,
            request=request,
            certificate=certificate,
            severity='INFO',
            details={
                'certificate_serial': certificate.serial_number,
                'cert_type': certificate.cert_type,
            }
        )
    
    def _log_auth_failure(self, request, reason, certificate_id):
        """Log failed certificate authentication."""
        PKIAuditLog.log(
            event_type='CERT_AUTH_FAILURE',
            description=f"Certificate authentication failed: {reason}",
            request=request,
            severity='WARNING',
            success=False,
            error_message=reason,
            details={
                'certificate_id': certificate_id,
            }
        )


class ChallengeResponseAuthBackend(BaseBackend):
    """
    Challenge-response authentication backend.
    
    This provides stronger authentication by requiring the client to
    sign a random challenge with their private key, proving possession
    of the private key.
    
    Flow:
    1. Client requests a challenge
    2. Server generates random nonce and stores it
    3. Client signs the nonce with their private key
    4. Server verifies the signature using the certificate's public key
    """
    
    def authenticate(self, request, certificate_pem=None,
                     challenge=None, signature=None,
                     pq_signature=None, **kwargs):
        """
        Authenticate using challenge-response.
        
        Args:
            request: HTTP request
            certificate_pem: Certificate in PEM format
            challenge: The challenge that was signed
            signature: Classical signature of the challenge
            pq_signature: Post-quantum signature (optional)
            
        Returns:
            User instance if authenticated, None otherwise
        """
        if not all([certificate_pem, challenge, signature]):
            return None
        
        try:
            # Load and verify certificate
            cert = ClassicalCrypto.load_certificate(certificate_pem)
            fingerprint = ClassicalCrypto.get_certificate_fingerprint(cert)
            
            user_cert = UserCertificate.objects.filter(
                fingerprint_sha256=fingerprint,
                status='ACTIVE'
            ).first()
            
            if not user_cert or not user_cert.is_valid():
                return None
            
            # Verify the signature
            public_key = cert.public_key()
            
            import base64
            challenge_bytes = base64.b64decode(challenge)
            signature_bytes = base64.b64decode(signature)
            
            if not ClassicalCrypto.verify_signature(
                public_key, signature_bytes, challenge_bytes
            ):
                self._log_auth_failure(
                    request, 
                    "Invalid challenge signature",
                    user_cert.serial_number
                )
                return None
            
            # Verify PQ signature if provided and certificate has PQ key
            if pq_signature and user_cert.has_pq_key and user_cert.pq_public_key:
                from ..crypto import PostQuantumCrypto
                
                pq_sig_bytes = base64.b64decode(pq_signature)
                
                if not PostQuantumCrypto.verify(
                    user_cert.pq_public_key,
                    challenge_bytes,
                    pq_sig_bytes,
                    user_cert.pq_algorithm
                ):
                    self._log_auth_failure(
                        request,
                        "Invalid PQ challenge signature",
                        user_cert.serial_number
                    )
                    return None
            
            user = user_cert.user
            
            if not user.is_active:
                return None
            
            user_cert.record_usage()
            self._log_auth_success(request, user, user_cert)
            
            return user
            
        except Exception as e:
            self._log_auth_failure(
                request,
                f"Challenge-response auth error: {str(e)}",
                "Unknown"
            )
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def _log_auth_success(self, request, user, certificate):
        PKIAuditLog.log(
            event_type='CERT_AUTH_SUCCESS',
            description=f"Challenge-response auth successful for {user.email}",
            user=user,
            request=request,
            certificate=certificate,
            severity='INFO',
            details={'method': 'challenge-response'}
        )
    
    def _log_auth_failure(self, request, reason, certificate_id):
        PKIAuditLog.log(
            event_type='CERT_AUTH_FAILURE',
            description=f"Challenge-response auth failed: {reason}",
            request=request,
            severity='WARNING',
            success=False,
            error_message=reason,
            details={
                'certificate_id': certificate_id,
                'method': 'challenge-response'
            }
        )
