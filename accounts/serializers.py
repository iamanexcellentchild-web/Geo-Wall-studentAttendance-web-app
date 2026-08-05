from rest_framework import serializers
from .models import User, PendingRegistration


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['teacher', 'student'])
    matric_or_staff_id = serializers.CharField(max_length=20)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists() or PendingRegistration.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists() or PendingRegistration.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_matric_or_staff_id(self, value):
        if User.objects.filter(matric_or_staff_id=value).exists() or PendingRegistration.objects.filter(matric_or_staff_id=value).exists():
            raise serializers.ValidationError("This ID is already registered.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_verified:
            raise serializers.ValidationError("Account not verified. Please verify your OTP first.")

        data['role'] = self.user.role
        data['email'] = self.user.email
        return data