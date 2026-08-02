from rest_framework import serializers
from .models import ClassSession, Attendance


class ClassSessionSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)

    class Meta:
        model = ClassSession
        fields = ('id', 'course', 'course_code', 'token', 'latitude', 'longitude',
                  'radius_meters', 'started_at', 'expires_at')
        read_only_fields = ('token', 'started_at', 'expires_at')


class JoinSessionSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=8)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class AttendanceSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)

    class Meta:
        model = Attendance
        fields = ('id', 'session', 'student', 'student_email', 'joined_at',
                  'distance_meters', 'within_geofence')
        read_only_fields = ('joined_at', 'distance_meters', 'within_geofence')