from django.contrib import admin
from .models import Group, Course, Room

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ['name', 'course', 'teacher', 'is_active', 'student_count']
    list_filter   = ['is_active', 'course', 'days']
    search_fields = ['name']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity']
