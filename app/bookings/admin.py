from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Booking
    """
    list_display = ['id', 'hotel', 'client', 'room', 'check_in_date', 'check_out_date', 'duration_days', 'status', 'payment_status', 'total_price']
    list_filter = ['hotel', 'status', 'payment_status', 'check_in_date', 'created_at']
    search_fields = ['client__first_name', 'client__last_name', 'client__email', 'room__number']
    list_editable = ['status', 'payment_status']
    readonly_fields = ['created_at', 'updated_at', 'confirmed_at', 'cancelled_at']
    
    fieldsets = (
        ('Información de la Reserva', {
            'fields': ('hotel', 'client', 'room', 'check_in_date', 'check_out_date', 'guests_count')
        }),
        ('Estado y Pagos', {
            'fields': ('status', 'payment_status', 'total_price')
        }),
        ('Información Adicional', {
            'fields': ('special_requests', 'cancellation_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request).select_related('hotel', 'client', 'room')
    
    def duration_days(self, obj):
        """Método para mostrar duración de la reserva"""
        return obj.duration
    duration_days.short_description = 'Días'
    
    def is_active_booking(self, obj):
        """Método para mostrar si la reserva está activa"""
        return obj.is_active
    is_active_booking.boolean = True
    is_active_booking.short_description = 'Activa'
    
    actions = ['confirm_bookings', 'cancel_bookings', 'mark_as_paid']

    def save_model(self, request, obj, form, change):
        # Bloquear creación de nuevas reservas si el hotel no acepta nuevas
        try:
            hotel_ref = obj.hotel or getattr(obj.room, 'hotel', None)
            if not change and hotel_ref and hasattr(hotel_ref, 'can_accept_new_bookings') and not hotel_ref.can_accept_new_bookings:
                self.message_user(request, 'El hotel no acepta nuevas reservas por su suscripción/estado.', level='error')
                return
        except Exception:
            pass
        super().save_model(request, obj, form, change)
    
    def confirm_bookings(self, request, queryset):
        """Acción para confirmar múltiples reservas"""
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{updated} reservas fueron confirmadas.')
    confirm_bookings.short_description = "Confirmar reservas seleccionadas"
    
    def cancel_bookings(self, request, queryset):
        """Acción para cancelar múltiples reservas"""
        updated = queryset.filter(status__in=['pending', 'confirmed']).update(status='cancelled')
        self.message_user(request, f'{updated} reservas fueron canceladas.')
    cancel_bookings.short_description = "Cancelar reservas seleccionadas"

    def mark_as_paid(self, request, queryset):
        """Acción para marcar reservas como pagadas"""
        updated_count = 0
        for booking in queryset:
            try:
                booking.payment_status = 'paid'
                # Si existe total_price, considerar como monto pagado
                if getattr(booking, 'total_price', None) is not None:
                    booking.paid_amount = booking.total_price
                booking.save(update_fields=['payment_status', 'paid_amount', 'updated_at'])
                updated_count += 1
            except Exception:
                continue
        self.message_user(request, f'{updated_count} reservas marcadas como pagadas.')
    mark_as_paid.short_description = "Marcar como pagadas"
