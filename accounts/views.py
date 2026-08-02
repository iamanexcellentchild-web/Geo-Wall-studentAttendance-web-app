from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User, OTP
from .serializers import RegisterSerializer, VerifyOTPSerializer, ResendOTPSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        otp = OTP.objects.create(user=user, code=OTP.generate_code())
        send_mail(
    'Your Geotend Verification Code',
    f'Your OTP code is: {otp.code}\n\nThis code will expire soon. If you did not request this, ignore this email.',
    None,
    [user.email],
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
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        otp = OTP.objects.filter(user=user, code=code, is_used=False).order_by('-created_at').first()
        if not otp:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
        otp.is_used = True
        otp.save()
        user.is_verified = True
        user.save()
        return Response({"message": "Account verified successfully."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_otp(request):
    serializer = ResendOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        if user.is_verified:
            return Response({"error": "Account already verified."}, status=status.HTTP_400_BAD_REQUEST)
        allowed, wait_seconds = OTP.can_resend(user)
        if not allowed:
            return Response(
                {"error": f"Please wait {wait_seconds} seconds before requesting a new OTP."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        otp = OTP.objects.create(user=user, code=OTP.generate_code())
        send_mail(
    'Your Geotend Verification Code (Resent)',
    f'Your new OTP code is: {otp.code}\n\nThis code will expire soon. If you did not request this, ignore this email.',
    None,
    [user.email],
)
        return Response({"message": "OTP resent. Check console."}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer