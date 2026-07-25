from django.db import models
from django.conf import settings


class Session(models.Model):
    course_code = models.CharField(max_length=20)
    course_title = models.CharField(max_length=100, blank=True)
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sessions_taught'
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_m = models.FloatField(default=40)
    code = models.CharField(max_length=10)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[('active', 'Active'), ('ended', 'Ended')],
        default='active'
    )

    def __str__(self):
        return f"{self.course_code} - {self.start_time.date()}"


class AttendanceRecord(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_records'
    )
    qr_token = models.CharField(max_length=255, unique=True)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    distance_m = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('present', 'Present'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student} - {self.session} - {self.status}"