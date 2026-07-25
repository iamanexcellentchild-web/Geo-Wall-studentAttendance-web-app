from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone

from .models import Session, AttendanceRecord
from .serializers import RequestQRSerializer, ScanSerializer
from .utils import generate_qr_token, verify_qr_token, haversine_distance


class RequestQRView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RequestQRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            session = Session.objects.get(id=data['session_id'], status='active')
        except Session.DoesNotExist:
            return Response({"detail": "Session not found or not active"}, status=status.HTTP_404_NOT_FOUND)

        distance = haversine_distance(
            data['latitude'], data['longitude'], session.latitude, session.longitude
        )
        if distance > session.radius_m:
            return Response({"detail": "Outside geofence"}, status=status.HTTP_403_FORBIDDEN)

        token = generate_qr_token(session.id, request.user.id)
        return Response({"qr_token": token})


class ScanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = ScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            session_id, student_id = verify_qr_token(data['qr_token'])
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if student_id != request.user.id:
            return Response({"detail": "Token does not belong to this user"}, status=status.HTTP_403_FORBIDDEN)

        session = Session.objects.select_for_update().get(id=session_id)

        record, created = AttendanceRecord.objects.select_for_update().get_or_create(
            session=session, student=request.user,
            defaults={'qr_token': data['qr_token']}
        )

        if record.used:
            return Response({"detail": "QR code already used"}, status=status.HTTP_400_BAD_REQUEST)

        distance = haversine_distance(
            data['latitude'], data['longitude'], session.latitude, session.longitude
        )
        if distance > session.radius_m:
            record.status = 'rejected'
            record.save()
            return Response({"detail": "Outside geofence"}, status=status.HTTP_403_FORBIDDEN)

        record.used = True
        record.used_at = timezone.now()
        record.latitude = data['latitude']
        record.longitude = data['longitude']
        record.distance_m = distance
        record.status = 'present'
        record.save()

        return Response({"detail": "Attendance marked", "status": "present"})