from django.contrib import admin

from .models import CustomUser, Subscribe


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'date_joined',
    )
    empty_value_display = '-пусто-'
    search_fields = ('username', 'email',)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'user', 'author',
    )
    empty_value_display = '-пусто-'
