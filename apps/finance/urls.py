from django.urls import path
from . import views
urlpatterns = [
    path('',                 views.finance_list,    name='finance'),
    path('create/',          views.payment_create,  name='payment-create'),
    path('<int:pk>/delete/', views.payment_delete,  name='payment-delete'),
    path('export/',          views.export_report,    name='finance-export'),
    path('export/period/',   views.export_period_report, name='finance-export-period'),
]
