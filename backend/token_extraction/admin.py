from django.contrib import admin
from .models import HubToken, TokenExtractionLog


@admin.register(HubToken)
class HubTokenAdmin(admin.ModelAdmin):
    list_display = ('user_login', 'user', 'expires_at', 'is_active', 'created_at', 'is_expired')
    list_filter = ('is_active', 'expires_at', 'created_at')
    search_fields = ('user_login', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'is_expired', 'time_until_expiry')
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'


@admin.register(TokenExtractionLog)
class TokenExtractionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'hub_login', 'status', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at')
    search_fields = ('user__email', 'hub_login')
    ordering = ('-started_at',)
    readonly_fields = ('started_at', 'completed_at')
