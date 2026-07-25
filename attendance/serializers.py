from rest_framework import serializers
from .models import Session, AttendanceRecord


class RequestQRSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class ScanSerializer(serializers.Serializer):
    qr_token = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()