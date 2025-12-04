/**
 * PKI API Configuration and Helper Functions
 */

import { urlApi } from './api';

// PKI API Endpoints
export const PKI_ENDPOINTS = {
    // Status
    STATUS: `${urlApi}api/pki/status/`,
    MY_CERTIFICATES: `${urlApi}api/pki/my-certificates/`,
    
    // Certificate Authority
    CA_LIST: `${urlApi}api/pki/ca/`,
    CA_DETAIL: (id) => `${urlApi}api/pki/ca/${id}/`,
    CA_CHAIN: (id) => `${urlApi}api/pki/ca/${id}/chain/`,
    CA_DOWNLOAD: (id) => `${urlApi}api/pki/ca/${id}/download_certificate/`,
    CA_CRL: (id) => `${urlApi}api/pki/ca/${id}/generate_crl/`,
    
    // Certificates
    CERT_LIST: `${urlApi}api/pki/certificates/`,
    CERT_DETAIL: (id) => `${urlApi}api/pki/certificates/${id}/`,
    CERT_DOWNLOAD: (id) => `${urlApi}api/pki/certificates/${id}/download/`,
    CERT_CHAIN: (id) => `${urlApi}api/pki/certificates/${id}/chain/`,
    CERT_REVOKE: (id) => `${urlApi}api/pki/certificates/${id}/revoke/`,
    
    // Certificate Requests
    REQUEST_LIST: `${urlApi}api/pki/requests/`,
    REQUEST_CREATE: `${urlApi}api/pki/requests/`,
    REQUEST_DETAIL: (id) => `${urlApi}api/pki/requests/${id}/`,
    REQUEST_APPROVE: (id) => `${urlApi}api/pki/requests/${id}/approve/`,
    REQUEST_REJECT: (id) => `${urlApi}api/pki/requests/${id}/reject/`,
    
    // CRL
    CRL_LIST: `${urlApi}api/pki/crl/`,
    CRL_DOWNLOAD: (id) => `${urlApi}api/pki/crl/${id}/download/`,
    
    // Authentication
    AUTH_CHECK: `${urlApi}api/pki/auth/`,
    AUTH_CHALLENGE: `${urlApi}api/pki/auth/challenge/`,
    AUTH_VERIFY: `${urlApi}api/pki/auth/verify/`,
    
    // PDF Operations
    PDF_SIGN: `${urlApi}api/pki/pdf/sign/`,
    PDF_VERIFY: `${urlApi}api/pki/pdf/verify/`,
    
    // Audit
    AUDIT_LIST: `${urlApi}api/pki/audit/`,
};

/**
 * Get authorization header with JWT token
 */
export const getAuthHeader = () => {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

/**
 * Make authenticated API request
 */
export const pkiRequest = async (url, options = {}) => {
    const headers = {
        ...getAuthHeader(),
        ...options.headers,
    };
    
    // Don't set Content-Type for FormData (browser sets it with boundary)
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    
    const response = await fetch(url, {
        ...options,
        headers,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error || error.detail || 'Request failed');
    }
    
    // Handle file downloads
    const contentType = response.headers.get('content-type');
    if (contentType && (contentType.includes('application/pdf') || 
                        contentType.includes('application/x-pem-file') ||
                        contentType.includes('application/x-x509'))) {
        return response.blob();
    }
    
    return response.json();
};

/**
 * Download file helper
 */
export const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
};
