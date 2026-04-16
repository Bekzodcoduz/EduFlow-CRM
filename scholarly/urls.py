from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "EduFlow"
admin.site.site_title = "EduFlow"
admin.site.index_title = "Boshqaruv paneli"

urlpatterns = [
    path('admin/',     admin.site.urls),
    path('',           include('apps.accounts.urls')),
    path('groups/',    include('apps.groups.urls')),
    path('students/',  include('apps.students.urls')),
    path('finance/',   include('apps.finance.urls')),
    path('reports/',   include('apps.reports.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('messaging/', include('apps.messaging.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
