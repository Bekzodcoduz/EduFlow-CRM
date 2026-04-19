from django.urls import path
from . import views
urlpatterns = [
    path('',                 views.finance_list,    name='finance'),
    path('create/',          views.payment_create,  name='payment-create'),
    path('export/',          views.export_report,    name='finance-export'),
    path('export/period/',   views.export_period_report, name='finance-export-period'),
]
