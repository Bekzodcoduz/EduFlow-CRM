from django.urls import path
from . import views
urlpatterns = [
    path('',                          views.attendance_home,   name='attendance'),
    path('toggle/',                   views.toggle_attendance, name='attendance-toggle'),
    path('mark-all/',                 views.mark_all,          name='attendance-mark-all'),
    path('report/<int:group_id>/',    views.attendance_report, name='attendance-report'),
]
