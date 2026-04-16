from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['student', 'course', 'payment_type', 'amount', 'received_by', 'created_at']
    list_filter   = ['payment_type']
    search_fields = ['student__first_name', 'student__last_name']
    readonly_fields = ['created_at']
