from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random


class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    matric_or_staff_id = models.CharField(max_length=20, unique=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} ({self.role})"


class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP for {self.user.email}"

    @staticmethod
    def generate_code():
        return str(random.randint(100000, 999999))

    @staticmethod
    def can_resend(user, cooldown_seconds=60):
        last_otp = OTP.objects.filter(user=user).order_by('-created_at').first()
        if not last_otp:
            return True, 0
        elapsed = (timezone.now() - last_otp.created_at).total_seconds()
        if elapsed >= cooldown_seconds:
            return True, 0
        return False, int(cooldown_seconds - elapsed)
    def is_expired(self, expiry_minutes=10):
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return elapsed > (expiry_minutes * 60)
class PendingRegistration(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # stored hashed
    role = models.CharField(max_length=10)
    matric_or_staff_id = models.CharField(max_length=20, unique=True)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self, expiry_minutes=10):
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return elapsed > (expiry_minutes * 60)

    def can_resend(self, cooldown_seconds=60):
        elapsed = (timezone.now() - self.last_sent_at).total_seconds()
        if elapsed >= cooldown_seconds:
            return True, 0
        return False, int(cooldown_seconds - elapsed)

    def __str__(self):
        return f"Pending: {self.email}"