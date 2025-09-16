#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de cancelación de reservas
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Agregar el directorio del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.bookings.models import Booking
from app.rooms.models import Room
from app.clients.models import Client
from app.core.services import EmailService

def test_cancellation_functionality():
    """Prueba la funcionalidad de cancelación de reservas"""
    print("🧪 Probando funcionalidad de cancelación de reservas...")
    
    try:
        # Buscar una reserva confirmada para cancelar
        booking = Booking.objects.filter(status='confirmed').first()
        
        if not booking:
            print("❌ No se encontraron reservas confirmadas para probar la cancelación")
            return False
        
        print(f"📋 Reserva encontrada: #{booking.id}")
        print(f"   - Habitación: {booking.room.number}")
        print(f"   - Cliente: {booking.client.full_name}")
        print(f"   - Estado actual: {booking.get_status_display()}")
        print(f"   - Fechas: {booking.check_in_date} - {booking.check_out_date}")
        
        # Estado de la habitación antes de cancelar
        room_status_before = booking.room.status
        print(f"   - Estado de habitación antes: {room_status_before}")
        
        # Cancelar la reserva
        print("\n🔄 Cancelando reserva...")
        success = booking.cancel_booking("Prueba de cancelación")
        
        if success:
            print("✅ Reserva cancelada exitosamente")
            print(f"   - Nuevo estado: {booking.get_status_display()}")
            print(f"   - Fecha de cancelación: {booking.cancelled_at}")
            print(f"   - Estado de habitación después: {booking.room.status}")
            
            # Verificar que la habitación esté disponible
            if booking.room.status == 'available':
                print("✅ Habitación marcada como disponible correctamente")
            else:
                print("❌ Error: La habitación no se marcó como disponible")
                return False
            
            # Probar envío de email de cancelación
            print("\n📧 Probando envío de email de cancelación...")
            email_result = EmailService.send_booking_cancellation(booking.id)
            
            if email_result.get('success'):
                print("✅ Email de cancelación enviado correctamente")
                print(f"   - Email enviado a: {email_result.get('recipient_email')}")
            else:
                print("⚠️  Email de cancelación no se pudo enviar:")
                print(f"   - Error: {email_result.get('message')}")
            
            return True
        else:
            print("❌ Error al cancelar la reserva")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        return False

def test_cancellation_validation():
    """Prueba las validaciones de cancelación"""
    print("\n🧪 Probando validaciones de cancelación...")
    
    try:
        # Buscar una reserva ya cancelada
        cancelled_booking = Booking.objects.filter(status='cancelled').first()
        
        if cancelled_booking:
            print(f"📋 Probando cancelar reserva ya cancelada: #{cancelled_booking.id}")
            success = cancelled_booking.cancel_booking()
            
            if not success:
                print("✅ Validación correcta: No se puede cancelar una reserva ya cancelada")
            else:
                print("❌ Error: Se permitió cancelar una reserva ya cancelada")
                return False
        
        # Buscar una reserva completada
        completed_booking = Booking.objects.filter(status='completed').first()
        
        if completed_booking:
            print(f"📋 Probando cancelar reserva completada: #{completed_booking.id}")
            success = completed_booking.cancel_booking()
            
            if not success:
                print("✅ Validación correcta: No se puede cancelar una reserva completada")
            else:
                print("❌ Error: Se permitió cancelar una reserva completada")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba de validaciones: {str(e)}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de cancelación de reservas")
    print("=" * 50)
    
    # Verificar que hay datos de prueba
    total_bookings = Booking.objects.count()
    print(f"📊 Total de reservas en la base de datos: {total_bookings}")
    
    if total_bookings == 0:
        print("❌ No hay reservas en la base de datos. Ejecuta primero el script de población de datos.")
        return
    
    # Ejecutar pruebas
    test1_passed = test_cancellation_functionality()
    test2_passed = test_cancellation_validation()
    
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"   - Prueba de cancelación: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   - Prueba de validaciones: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ La funcionalidad de cancelación está funcionando correctamente")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa los errores anteriores.")
    
    print("\n💡 Para probar la funcionalidad completa:")
    print("   1. Ejecuta el servidor: python manage.py runserver")
    print("   2. Ve a http://localhost:8000/portal/")
    print("   3. Inicia sesión con un usuario que tenga reservas")
    print("   4. Ve a 'Mis Reservas' y prueba cancelar una reserva")

if __name__ == "__main__":
    main()
