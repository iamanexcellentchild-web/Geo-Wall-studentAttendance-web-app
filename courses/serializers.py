from rest_framework import serializers
from .models import Course, Enrollment


class CourseSerializer(serializers.ModelSerializer):
    teacher_email = serializers.EmailField(source='teacher.email', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'code', 'title', 'teacher', 'teacher_email', 'join_code', 'created_at')
        read_only_fields = ('teacher', 'join_code', 'created_at')


class EnrollmentSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'course', 'course_code', 'student', 'student_email', 'enrolled_at')
        read_only_fields = ('student', 'enrolled_at')


class JoinCourseSerializer(serializers.Serializer):
    join_code = serializers.CharField(max_length=8)