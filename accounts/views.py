from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User, OTP, PendingRegistration
from .serializers import RegisterSerializer, VerifyOTPSerializer, ResendOTPSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.utils import timezone

@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        code = OTP.generate_code()

        pending = PendingRegistration.objects.create(
            username=data['username'],
            email=data['email'],
            password=make_password(data['password']),
            role=data['role'],
            matric_or_staff_id=data['matric_or_staff_id'],
            otp_code=code
        )

        send_mail(
            'Your Geotend Verification Code',
            f'Your OTP code is: {code}\n\nThis code will expire soon. If you did not request this, ignore this email.',
            None,
            [pending.email],
        )

        return Response(
            {"message": "Registered. Check your email for the OTP."},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_otp(request):
    serializer = VerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            pending = PendingRegistration.objects.get(email=email)
        except PendingRegistration.DoesNotExist:
            return Response({"error": "No pending registration found for this email."}, status=status.HTTP_404_NOT_FOUND)

        if pending.otp_code != code:
            return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if pending.is_expired():
            pending.delete()
            return Response({"error": "OTP has expired. Please register again."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            username=pending.username,
            email=pending.email,
            password=pending.password,
            role=pending.role,
            matric_or_staff_id=pending.matric_or_staff_id,
            is_verified=True
        )
        pending.delete()

        return Response({"message": "Account verified successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_otp(request):
    serializer = ResendOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            pending = PendingRegistration.objects.get(email=email)
        except PendingRegistration.DoesNotExist:
            return Response({"error": "No pending registration found for this email."}, status=status.HTTP_404_NOT_FOUND)

        allowed, wait_seconds = pending.can_resend()
        if not allowed:
            return Response(
                {"error": f"Please wait {wait_seconds} seconds before requesting a new OTP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        pending.otp_code = OTP.generate_code()
        pending.last_sent_at = timezone.now()
        pending.save()

        send_mail(
            'Your Geotend Verification Code (Resent)',
            f'Your new OTP code is: {pending.otp_code}\n\nThis code will expire soon. If you did not request this, ignore this email.',
            None,
            [pending.email],
        )
        return Response({"message": "OTP resent. Check your email."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer