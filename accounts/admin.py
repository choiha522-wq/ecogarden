from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('생태정원 재화', {'fields': ('points', 'tickets', 'nutrients', 'friend_code')}),
    )
    list_display = ('username', 'email', 'points', 'tickets', 'nutrients', 'is_staff')
