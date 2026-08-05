from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP, PendingRegistration

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'matric_or_staff_id', 'is_verified', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('role', 'matric_or_staff_id', 'is_verified')}),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(OTP)
admin.site.register(PendingRegistration)