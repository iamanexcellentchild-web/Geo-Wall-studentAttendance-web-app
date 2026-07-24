from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'matric_or_staff_id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        if not validated_data.get('matric_or_staff_id'):
            validated_data['matric_or_staff_id'] = None
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.is_email_verified = False
        user.save()
        return user