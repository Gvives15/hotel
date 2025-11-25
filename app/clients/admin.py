from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Client
    """
    list_display = ['full_name', 'hotel', 'email', 'phone', 'dni', 'active', 'vip', 'booking_count']
    list_filter = ['hotel', 'active', 'vip', 'nationality', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'dni', 'phone']
    list_editable = ['active', 'vip']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_active', 'mark_inactive', 'mark_vip', 'unmark_vip']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('hotel', 'first_name', 'last_name', 'email', 'phone', 'dni')
        }),
        ('Información Adicional', {
            'fields': ('address', 'birth_date', 'nationality')
        }),
        ('Estado', {
            'fields': ('active', 'vip')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request)
    
    def booking_count(self, obj):
        """Método para mostrar cantidad de reservas del cliente"""
        return obj.booking_set.count()
    booking_count.short_description = 'Reservas'

    def mark_active(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} clientes marcados como activos.')
    mark_active.short_description = 'Marcar como activos'

    def mark_inactive(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} clientes marcados como inactivos.')
    mark_inactive.short_description = 'Marcar como inactivos'

    def mark_vip(self, request, queryset):
        updated = queryset.update(vip=True)
        self.message_user(request, f'{updated} clientes marcados como VIP.')
    mark_vip.short_description = 'Marcar como VIP'

    def unmark_vip(self, request, queryset):
        updated = queryset.update(vip=False)
        self.message_user(request, f'{updated} clientes desmarcados como VIP.')
    unmark_vip.short_description = 'Quitar VIP'
