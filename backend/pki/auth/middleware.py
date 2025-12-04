"""
Client Certificate Middleware

Extracts client certificate information from HTTP headers
(set by reverse proxy during TLS handshake) and makes it
available in the request object.
"""

import base64
import re
from django.utils.deprecation import MiddlewareMixin


class ClientCertificateMiddleware(MiddlewareMixin):
    """
    Middleware to extract client certificate from proxy headers.
    
    When using nginx or apache as a reverse proxy with client
    certificate authentication, the certificate is passed to
    Django via headers.
    
    Nginx configuration example:
    ```
    ssl_client_certificate /path/to/ca-chain.pem;
    ssl_verify_client optional;
    
    location / {
        proxy_set_header X-SSL-Client-Cert $ssl_client_escaped_cert;
        proxy_set_header X-SSL-Client-Verify $ssl_client_verify;
        proxy_set_header X-SSL-Client-S-DN $ssl_client_s_dn;
        proxy_set_header X-SSL-Client-I-DN $ssl_client_i_dn;
        proxy_set_header X-SSL-Client-Serial $ssl_client_serial;
        proxy_set_header X-SSL-Client-Fingerprint $ssl_client_fingerprint;
        ...
    }
    ```
    
    Apache configuration example:
    ```
    SSLVerifyClient optional
    SSLOptions +StdEnvVars +ExportCertData
    
    RequestHeader set X-SSL-Client-Cert "%{SSL_CLIENT_CERT}e"
    RequestHeader set X-SSL-Client-Verify "%{SSL_CLIENT_VERIFY}e"
    RequestHeader set X-SSL-Client-S-DN "%{SSL_CLIENT_S_DN}e"
    ```
    """
    
    # Header names (can be customized)
    HEADER_CERT = 'HTTP_X_SSL_CLIENT_CERT'
    HEADER_VERIFY = 'HTTP_X_SSL_CLIENT_VERIFY'
    HEADER_SUBJECT_DN = 'HTTP_X_SSL_CLIENT_S_DN'
    HEADER_ISSUER_DN = 'HTTP_X_SSL_CLIENT_I_DN'
    HEADER_SERIAL = 'HTTP_X_SSL_CLIENT_SERIAL'
    HEADER_FINGERPRINT = 'HTTP_X_SSL_CLIENT_FINGERPRINT'
    HEADER_NOT_BEFORE = 'HTTP_X_SSL_CLIENT_V_START'
    HEADER_NOT_AFTER = 'HTTP_X_SSL_CLIENT_V_END'
    
    def process_request(self, request):
        """
        Extract certificate information and attach to request.
        
        Adds `request.client_cert` dict with certificate details.
        """
        # Initialize client cert info
        request.client_cert = {
            'provided': False,
            'verified': False,
            'certificate_pem': None,
            'subject_dn': None,
            'issuer_dn': None,
            'serial': None,
            'fingerprint': None,
            'not_before': None,
            'not_after': None,
        }
        
        # Check if certificate was provided
        verify_status = request.META.get(self.HEADER_VERIFY, '')
        if verify_status in ('SUCCESS', 'NONE', 'GENEROUS'):
            # Check for certificate in headers
            cert_header = request.META.get(self.HEADER_CERT, '')
            
            if cert_header:
                request.client_cert['provided'] = True
                request.client_cert['verified'] = (verify_status == 'SUCCESS')
                
                # Decode certificate (may be URL-encoded)
                request.client_cert['certificate_pem'] = self._decode_cert(cert_header)
                
                # Extract other fields
                request.client_cert['subject_dn'] = request.META.get(
                    self.HEADER_SUBJECT_DN, ''
                )
                request.client_cert['issuer_dn'] = request.META.get(
                    self.HEADER_ISSUER_DN, ''
                )
                request.client_cert['serial'] = request.META.get(
                    self.HEADER_SERIAL, ''
                )
                request.client_cert['fingerprint'] = self._normalize_fingerprint(
                    request.META.get(self.HEADER_FINGERPRINT, '')
                )
                request.client_cert['not_before'] = request.META.get(
                    self.HEADER_NOT_BEFORE, ''
                )
                request.client_cert['not_after'] = request.META.get(
                    self.HEADER_NOT_AFTER, ''
                )
    
    def _decode_cert(self, cert_header):
        """
        Decode certificate from header value.
        
        Nginx URL-encodes the certificate, so we need to decode it.
        """
        import urllib.parse
        
        # URL decode
        cert = urllib.parse.unquote(cert_header)
        
        # Remove any extra whitespace
        cert = cert.strip()
        
        # Ensure proper PEM format
        if not cert.startswith('-----BEGIN'):
            # Try to reconstruct PEM format
            cert = '-----BEGIN CERTIFICATE-----\n' + cert + '\n-----END CERTIFICATE-----'
        
        return cert
    
    def _normalize_fingerprint(self, fingerprint):
        """
        Normalize fingerprint format (remove colons, uppercase).
        """
        if not fingerprint:
            return None
        
        # Remove colons and spaces, uppercase
        return re.sub(r'[:\s]', '', fingerprint).upper()


class TrustedProxyMiddleware(MiddlewareMixin):
    """
    Middleware to validate that certificate headers come from trusted proxies.
    
    This is a security measure to prevent header spoofing attacks.
    Only accept certificate headers from configured trusted proxy IPs.
    """
    
    # Trusted proxy IPs (configure in settings)
    TRUSTED_PROXIES = []  # Will be loaded from settings
    
    # Headers that should only be trusted from proxies
    PROTECTED_HEADERS = [
        'HTTP_X_SSL_CLIENT_CERT',
        'HTTP_X_SSL_CLIENT_VERIFY',
        'HTTP_X_SSL_CLIENT_S_DN',
        'HTTP_X_SSL_CLIENT_I_DN',
        'HTTP_X_SSL_CLIENT_SERIAL',
        'HTTP_X_SSL_CLIENT_FINGERPRINT',
    ]
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        from django.conf import settings
        self.TRUSTED_PROXIES = getattr(settings, 'TRUSTED_PROXIES', ['127.0.0.1'])
    
    def process_request(self, request):
        """
        Strip certificate headers if not from trusted proxy.
        """
        remote_addr = request.META.get('REMOTE_ADDR', '')
        
        # Check X-Forwarded-For for the actual client IP
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            # Get the first (client) IP
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = remote_addr
        
        # If request is not from trusted proxy, remove protected headers
        if remote_addr not in self.TRUSTED_PROXIES:
            for header in self.PROTECTED_HEADERS:
                if header in request.META:
                    del request.META[header]
