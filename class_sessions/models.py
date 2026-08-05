from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string
import math
from courses.models import Course


class ClassSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=8, unique=True, blank=True)
    rotating_code = models.CharField(max_length=8, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_meters = models.FloatField(default=50)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_active(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"{self.course.code} session ({self.token})"


class Attendance(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances')
    joined_at = models.DateTimeField(auto_now_add=True)
    distance_meters = models.FloatField()
    within_geofence = models.BooleanField()

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.email} - {self.session}"


def haversine_distance(lat1, lon1, lat2, lon2):
    """Returns distance in meters between two GPS points."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c