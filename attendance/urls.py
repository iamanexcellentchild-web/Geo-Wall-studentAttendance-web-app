from django.urls import path
from .views import RequestQRView, ScanView

urlpatterns = [
    path('request-qr/', RequestQRView.as_view(), name='request-qr'),
    path('scan/', ScanView.as_view(), name='scan'),
]