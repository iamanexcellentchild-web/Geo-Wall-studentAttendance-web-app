from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from courses.models import Course, Enrollment
from .models import ClassSession, Attendance, haversine_distance
from .serializers import ClassSessionSerializer, JoinSessionSerializer, AttendanceSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request):
    if request.user.role != 'teacher':
        return Response({"error": "Only teachers can start sessions."}, status=status.HTTP_403_FORBIDDEN)

    course_id = request.data.get('course')
    try:
        course = Course.objects.get(id=course_id, teacher=request.user)
    except Course.DoesNotExist:
        return Response({"error": "Course not found or not yours."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ClassSessionSerializer(data=request.data)
    if serializer.is_valid():
        session = serializer.save(course=course)
        return Response(ClassSessionSerializer(session).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_session(request):
    if request.user.role != 'student':
        return Response({"error": "Only students can join sessions."}, status=status.HTTP_403_FORBIDDEN)

    serializer = JoinSessionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data['token']
    lat = serializer.validated_data['latitude']
    lng = serializer.validated_data['longitude']

    try:
        session = ClassSession.objects.get(token=token)
    except ClassSession.DoesNotExist:
        return Response({"error": "Invalid session token."}, status=status.HTTP_404_NOT_FOUND)

    if not session.is_active():
        return Response({"error": "This session has expired."}, status=status.HTTP_400_BAD_REQUEST)

    if not Enrollment.objects.filter(course=session.course, student=request.user).exists():
        return Response({"error": "You are not enrolled in this course."}, status=status.HTTP_403_FORBIDDEN)

    if Attendance.objects.filter(session=session, student=request.user).exists():
        return Response({"error": "Already marked present for this session."}, status=status.HTTP_400_BAD_REQUEST)

    distance = haversine_distance(session.latitude, session.longitude, lat, lng)
    within_geofence = distance <= session.radius_meters

    attendance = Attendance.objects.create(
        session=session,
        student=request.user,
        distance_meters=distance,
        within_geofence=within_geofence
    )

    if not within_geofence:
        return Response({
            "warning": "You are outside the allowed classroom radius. Attendance flagged for review.",
            "distance_meters": round(distance, 1),
            "data": AttendanceSerializer(attendance).data
        }, status=status.HTTP_200_OK)

    return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_attendance(request, session_id):
    try:
        session = ClassSession.objects.get(id=session_id)
    except ClassSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'teacher' or session.course.teacher != request.user:
        return Response({"error": "Not authorized to view this."}, status=status.HTTP_403_FORBIDDEN)

    attendances = Attendance.objects.filter(session=session)
    serializer = AttendanceSerializer(attendances, many=True)
    return Response(serializer.data)