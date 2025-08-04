from django.contrib import admin
from .models import EmailLog

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_email', 'recipient_name', 'subject', 'status', 'sent_at', 'created_at')
    list_filter = ('status', 'sent_at', 'created_at')
    search_fields = ('recipient_email', 'recipient_name', 'subject')
    readonly_fields = ('created_at', 'sent_at', 'error_message')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Información del Email', {
            'fields': ('recipient_email', 'recipient_name', 'subject', 'content')
        }),
        ('Estado y Tracking', {
            'fields': ('status', 'sent_at', 'error_message')
        }),
        ('Relaciones', {
            'fields': ('booking', 'client'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """No permitir crear registros manualmente desde el admin"""
        return False
