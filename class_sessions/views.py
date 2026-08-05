import csv
from django.http import HttpResponse
from django.core.mail import send_mail
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

        enrolled_students = Enrollment.objects.filter(course=course).select_related('student')
        for enrollment in enrolled_students:
            send_mail(
                f'Attendance Session Started: {course.code}',
                f'A new attendance session has started for {course.title} ({course.code}).\n\n'
                f'Join code: {session.token}\n\n'
                f'This session expires at {session.expires_at.strftime("%H:%M")}.',
                None,
                [enrollment.student.email],
            )

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_attendance_csv(request, session_id):
    try:
        session = ClassSession.objects.get(id=session_id)
    except ClassSession.DoesNotExist:
        return Response({"error": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'teacher' or session.course.teacher != request.user:
        return Response({"error": "Not authorized to export this."}, status=status.HTTP_403_FORBIDDEN)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{session.course.code}_{session.token}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student Email', 'Joined At', 'Distance (meters)', 'Within Geofence'])

    attendances = Attendance.objects.filter(session=session)
    for record in attendances:
        writer.writerow([
            record.student.email,
            record.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
            round(record.distance_meters, 1),
            'Yes' if record.within_geofence else 'No'
        ])

    return response
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_analytics(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.user.role != 'teacher' or course.teacher != request.user:
        return Response({"error": "Not authorized to view this."}, status=status.HTTP_403_FORBIDDEN)

    sessions = ClassSession.objects.filter(course=course)
    total_sessions = sessions.count()

    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    total_students = enrollments.count()

    student_data = []
    total_attended_all = 0

    for enrollment in enrollments:
        student = enrollment.student
        attendances = Attendance.objects.filter(session__course=course, student=student)
        sessions_attended = attendances.count()
        flagged_count = attendances.filter(within_geofence=False).count()

        attendance_rate = round((sessions_attended / total_sessions * 100), 1) if total_sessions > 0 else 0.0
        total_attended_all += sessions_attended

        student_data.append({
            "email": student.email,
            "sessions_attended": sessions_attended,
            "attendance_rate": attendance_rate,
            "flagged_count": flagged_count,
        })

    overall_attendance_rate = 0.0
    if total_sessions > 0 and total_students > 0:
        overall_attendance_rate = round((total_attended_all / (total_sessions * total_students) * 100), 1)

    return Response({
        "course": course.code,
        "total_sessions": total_sessions,
        "total_students": total_students,
        "overall_attendance_rate": overall_attendance_rate,
        "students": student_data,
    })