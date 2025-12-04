"""
PKI URL Configuration

Maps API endpoints to views.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'ca', views.CertificateAuthorityViewSet, basename='ca')
router.register(r'certificates', views.UserCertificateViewSet, basename='certificate')
router.register(r'requests', views.CertificateRequestViewSet, basename='certificate-request')
router.register(r'crl', views.CRLViewSet, basename='crl')
router.register(r'audit', views.PKIAuditLogViewSet, basename='audit')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Status/Info
    path('status/', views.pki_status, name='pki-status'),
    path('my-certificates/', views.my_certificates, name='my-certificates'),
    
    # Authentication
    path('auth/', views.CertificateAuthView.as_view(), name='cert-auth'),
    path('auth/challenge/', views.ChallengeAuthView.as_view(), name='challenge-auth'),
    path('auth/verify/', views.ChallengeVerifyView.as_view(), name='challenge-verify'),
    
    # PDF Operations
    path('pdf/sign/', views.PDFSignView.as_view(), name='pdf-sign'),
    path('pdf/verify/', views.PDFVerifyView.as_view(), name='pdf-verify'),
]
