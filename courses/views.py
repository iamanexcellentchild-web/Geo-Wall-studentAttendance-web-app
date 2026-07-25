from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Enrollment
from .serializers import CourseSerializer, EnrollmentSerializer, JoinCourseSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def course_list_create(request):
    if request.method == 'GET':
        if request.user.role == 'teacher':
            courses = Course.objects.filter(teacher=request.user)
        else:
            courses = Course.objects.filter(enrollments__student=request.user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        if request.user.role != 'teacher':
            return Response({"error": "Only teachers can create courses."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll_course(request):
    if request.user.role != 'student':
        return Response({"error": "Only students can enroll in courses."}, status=status.HTTP_403_FORBIDDEN)

    serializer = JoinCourseSerializer(data=request.data)
    if serializer.is_valid():
        join_code = serializer.validated_data['join_code']

        try:
            course = Course.objects.get(join_code=join_code)
        except Course.DoesNotExist:
            return Response({"error": "Invalid join code."}, status=status.HTTP_404_NOT_FOUND)

        if Enrollment.objects.filter(course=course, student=request.user).exists():
            return Response({"error": "Already enrolled in this course."}, status=status.HTTP_400_BAD_REQUEST)

        enrollment = Enrollment.objects.create(course=course, student=request.user)
        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_students(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'teacher' or course.teacher != request.user:
        return Response({"error": "Not authorized to view this roster."}, status=status.HTTP_403_FORBIDDEN)

    enrollments = Enrollment.objects.filter(course=course)
    serializer = EnrollmentSerializer(enrollments, many=True)
    return Response(serializer.data)