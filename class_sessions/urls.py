from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_session, name='start_session'),
    path('join/', views.join_session, name='join_session'),
    path('<int:session_id>/attendance/', views.session_attendance, name='session_attendance'),
    path('<int:session_id>/attendance/export/', views.export_attendance_csv, name='export_attendance_csv'),
    path('course/<int:course_id>/analytics/', views.course_analytics, name='course_analytics'),
]