from django.urls import path
from . import views

urlpatterns = [
    path('',               views.group_list,   name='groups'),
    path('<int:pk>/',      views.group_detail, name='group-detail'),
    path('create/',        views.group_create, name='group-create'),
    path('<int:pk>/edit/', views.group_edit,   name='group-edit'),
    path('<int:pk>/toggle/', views.group_toggle, name='group-toggle'),
    path('<int:pk>/delete/', views.group_delete, name='group-delete'),
]
