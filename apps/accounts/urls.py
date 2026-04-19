from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.dashboard_view,  name='dashboard'),
    path('dashboard/partial-payments/',   views.partial_payments_view, name='dashboard-partial-payments'),
    path('login/',                        views.login_view,      name='login'),
    path('logout/',                       views.logout_view,     name='logout'),
    path('settings/',                     views.account_settings, name='settings'),
    path('teachers/',                     views.teachers_list,   name='teachers'),
    path('teachers/create/',             views.teacher_create,  name='teacher-create'),
    path('teachers/<int:pk>/',           views.teacher_detail,  name='teacher-detail'),
    path(
        'teachers/<int:pk>/month-expectation/',
        views.teacher_month_expectation,
        name='teacher-month-expectation',
    ),
    path('teachers/<int:pk>/set-password/', views.teacher_set_password, name='teacher-set-password'),
    path('teachers/<int:pk>/credentials/', views.teacher_update_credentials, name='teacher-update-credentials'),
    path('teachers/<int:pk>/delete/',    views.teacher_delete,  name='teacher-delete'),
]
