from django.contrib import admin
from .models import Session, AttendanceRecord

admin.site.register(Session)
admin.site.register(AttendanceRecord)