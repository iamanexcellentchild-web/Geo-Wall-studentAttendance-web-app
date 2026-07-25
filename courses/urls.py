from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list_create, name='course_list_create'),
    path('enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/students/', views.course_students, name='course_students'),
]