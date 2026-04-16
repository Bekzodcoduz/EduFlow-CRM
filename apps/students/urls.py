from django.urls import path
from . import views
urlpatterns = [
    path('',                    views.student_list,   name='students'),
    path('create/',             views.student_create, name='student-create'),
    path('<int:pk>/',           views.student_detail, name='student-detail'),
    path('<int:pk>/contact/',   views.student_update_contact, name='student-update-contact'),
    path('<int:pk>/delete/',    views.student_delete, name='student-delete'),
]
