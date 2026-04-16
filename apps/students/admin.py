from django.contrib import admin
from .models import Student, Attendance

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'phone', 'group', 'balance', 'is_active', 'region']
    list_filter   = ['is_active', 'region', 'group__course']
    search_fields = ['first_name', 'last_name', 'phone']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'is_present']
    list_filter  = ['is_present', 'date']
