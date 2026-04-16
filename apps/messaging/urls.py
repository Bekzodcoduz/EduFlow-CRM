from django.urls import path
from . import views

urlpatterns = [
    path('', views.sms_compose, name='messaging-sms'),
]
