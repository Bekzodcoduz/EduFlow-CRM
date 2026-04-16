from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as Base
from .models import User

@admin.register(User)
class UserAdmin(Base):
    list_display  = ['username', 'full_name', 'role', 'phone', 'is_active']
    list_filter   = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name']
    fieldsets = Base.fieldsets + (
        ("EduFlow", {'fields': ('role', 'phone', 'subject', 'experience')}),
    )
