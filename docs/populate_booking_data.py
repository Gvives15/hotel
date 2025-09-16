#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de ejemplo para el sistema de reservas
"""

import os
import sys
import django
from datetime import date, timedelta

# Configurar Django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from app.rooms.models import Room
from app.clients.models import Client
from app.bookings.models import Booking
from django.contrib.auth.models import User

def create_rooms():
    """Crear habitaciones de ejemplo"""
    print("Creando habitaciones...")
    
    rooms_data = [
        {
            'number': '101',
            'type': 'individual',
            'capacity': 1,
            'price': 80.00,
            'description': 'Habitación individual con vista al jardín, perfecta para viajeros solos.',
            'floor': 1,
            'status': 'available'
        },
        {
            'number': '102',
            'type': 'double',
            'capacity': 2,
            'price': 120.00,
            'description': 'Habitación doble espaciosa con cama king-size y balcón privado.',
            'floor': 1,
            'status': 'available'
        },
        {
            'number': '201',
            'type': 'double',
            'capacity': 2,
            'price': 130.00,
            'description': 'Habitación doble en el segundo piso con vista panorámica de la ciudad.',
            'floor': 2,
            'status': 'available'
        },
        {
            'number': '202',
            'type': 'triple',
            'capacity': 3,
            'price': 180.00,
            'description': 'Habitación triple ideal para familias pequeñas o grupos de amigos.',
            'floor': 2,
            'status': 'available'
        },
        {
            'number': '301',
            'type': 'suite',
            'capacity': 4,
            'price': 250.00,
            'description': 'Suite de lujo con sala de estar separada, jacuzzi y vista premium.',
            'floor': 3,
            'status': 'available'
        },
        {
            'number': '302',
            'type': 'family',
            'capacity': 6,
            'price': 300.00,
            'description': 'Habitación familiar con múltiples camas y espacio amplio para grupos grandes.',
            'floor': 3,
            'status': 'available'
        },
        {
            'number': '401',
            'type': 'suite',
            'capacity': 2,
            'price': 280.00,
            'description': 'Suite ejecutiva con escritorio, sala de reuniones y servicios premium.',
            'floor': 4,
            'status': 'available'
        },
        {
            'number': '402',
            'type': 'individual',
            'capacity': 1,
            'price': 90.00,
            'description': 'Habitación individual moderna con diseño minimalista y tecnología avanzada.',
            'floor': 4,
            'status': 'available'
        }
    ]
    
    created_rooms = []
    for room_data in rooms_data:
        room, created = Room.objects.get_or_create(
            number=room_data['number'],
            defaults=room_data
        )
        if created:
            print(f"  ✓ Habitación {room.number} creada")
        else:
            print(f"  - Habitación {room.number} ya existe")
        created_rooms.append(room)
    
    return created_rooms

def create_sample_clients():
    """Crear clientes de ejemplo"""
    print("Creando clientes de ejemplo...")
    
    clients_data = [
        {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan.perez@email.com',
            'phone': '+34 600 123 456',
            'dni': '12345678A',
            'address': 'Calle Mayor 123, Madrid',
            'nationality': 'Español'
        },
        {
            'first_name': 'María',
            'last_name': 'García',
            'email': 'maria.garcia@email.com',
            'phone': '+34 600 234 567',
            'dni': '23456789B',
            'address': 'Avenida Principal 456, Barcelona',
            'nationality': 'Español'
        },
        {
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'email': 'carlos.rodriguez@email.com',
            'phone': '+34 600 345 678',
            'dni': '34567890C',
            'address': 'Plaza Central 789, Valencia',
            'nationality': 'Español'
        },
        {
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'email': 'ana.martinez@email.com',
            'phone': '+34 600 456 789',
            'dni': '45678901D',
            'address': 'Calle Nueva 321, Sevilla',
            'nationality': 'Español'
        },
        {
            'first_name': 'Luis',
            'last_name': 'López',
            'email': 'luis.lopez@email.com',
            'phone': '+34 600 567 890',
            'dni': '56789012E',
            'address': 'Avenida del Mar 654, Málaga',
            'nationality': 'Español'
        }
    ]
    
    created_clients = []
    for client_data in clients_data:
        client, created = Client.objects.get_or_create(
            email=client_data['email'],
            defaults=client_data
        )
        if created:
            print(f"  ✓ Cliente {client.full_name} creado")
        else:
            print(f"  - Cliente {client.full_name} ya existe")
        created_clients.append(client)
    
    return created_clients

def create_sample_bookings(rooms, clients):
    """Crear reservas de ejemplo"""
    print("Creando reservas de ejemplo...")
    
    # Crear algunas reservas pasadas y futuras
    today = date.today()
    
    bookings_data = [
        {
            'client': clients[0],
            'room': rooms[0],
            'check_in_date': today - timedelta(days=30),
            'check_out_date': today - timedelta(days=28),
            'status': 'completed',
            'payment_status': 'paid',
            'guests_count': 1,
            'special_requests': 'Habitación con vista al jardín si es posible',
            'total_price': 160.00
        },
        {
            'client': clients[1],
            'room': rooms[1],
            'check_in_date': today - timedelta(days=15),
            'check_out_date': today - timedelta(days=12),
            'status': 'completed',
            'payment_status': 'paid',
            'guests_count': 2,
            'special_requests': 'Cama king-size preferiblemente',
            'total_price': 360.00
        },
        {
            'client': clients[2],
            'room': rooms[2],
            'check_in_date': today + timedelta(days=5),
            'check_out_date': today + timedelta(days=8),
            'status': 'confirmed',
            'payment_status': 'pending',
            'guests_count': 2,
            'special_requests': 'Vista panorámica si está disponible',
            'total_price': 390.00
        },
        {
            'client': clients[3],
            'room': rooms[3],
            'check_in_date': today + timedelta(days=10),
            'check_out_date': today + timedelta(days=13),
            'status': 'confirmed',
            'payment_status': 'pending',
            'guests_count': 3,
            'special_requests': 'Habitación cerca del ascensor',
            'total_price': 540.00
        },
        {
            'client': clients[4],
            'room': rooms[4],
            'check_in_date': today + timedelta(days=20),
            'check_out_date': today + timedelta(days=22),
            'status': 'pending',
            'payment_status': 'pending',
            'guests_count': 2,
            'special_requests': 'Suite con jacuzzi',
            'total_price': 500.00
        }
    ]
    
    created_bookings = []
    for booking_data in bookings_data:
        # Verificar si ya existe una reserva similar
        existing_booking = Booking.objects.filter(
            client=booking_data['client'],
            room=booking_data['room'],
            check_in_date=booking_data['check_in_date']
        ).first()
        
        if existing_booking:
            print(f"  - Reserva para {booking_data['client'].full_name} ya existe")
            created_bookings.append(existing_booking)
        else:
            try:
                # Crear la reserva sin validación automática
                booking = Booking(
                    client=booking_data['client'],
                    room=booking_data['room'],
                    check_in_date=booking_data['check_in_date'],
                    check_out_date=booking_data['check_out_date'],
                    status=booking_data['status'],
                    payment_status=booking_data['payment_status'],
                    guests_count=booking_data['guests_count'],
                    special_requests=booking_data['special_requests'],
                    total_price=booking_data['total_price']
                )
                # Guardar sin validación
                booking.save(skip_validation=True)
                print(f"  ✓ Reserva #{booking.id} creada para {booking.client.full_name}")
                created_bookings.append(booking)
            except Exception as e:
                print(f"  ✗ Error creando reserva para {booking_data['client'].full_name}: {str(e)}")
    
    return created_bookings
    
    return created_bookings

def create_test_user():
    """Crear usuario de prueba"""
    print("Creando usuario de prueba...")
    
    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@o11ce.com',
            'first_name': 'Usuario',
            'last_name': 'Prueba',
            'is_staff': False,
            'is_active': True
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("  ✓ Usuario de prueba creado (username: testuser, password: testpass123)")
    else:
        print("  - Usuario de prueba ya existe")
    
    # Crear cliente asociado al usuario
    client, created = Client.objects.get_or_create(
        user=user,
        defaults={
            'first_name': 'Usuario',
            'last_name': 'Prueba',
            'email': 'test@o11ce.com',
            'phone': '+34 600 999 999',
            'dni': '99999999Z',
            'address': 'Calle de Prueba 999, Test City',
            'nationality': 'Español'
        }
    )
    
    if created:
        print("  ✓ Cliente de prueba creado")
    else:
        print("  - Cliente de prueba ya existe")
    
    return user, client

def main():
    """Función principal"""
    print("=== Poblando base de datos con datos de ejemplo ===\n")
    
    try:
        # Crear habitaciones
        rooms = create_rooms()
        print()
        
        # Crear clientes
        clients = create_sample_clients()
        print()
        
        # Crear reservas
        bookings = create_sample_bookings(rooms, clients)
        print()
        
        # Crear usuario de prueba
        user, client = create_test_user()
        print()
        
        print("=== Resumen ===")
        print(f"Habitaciones creadas: {len(rooms)}")
        print(f"Clientes creados: {len(clients)}")
        print(f"Reservas creadas: {len(bookings)}")
        print(f"Usuario de prueba: {user.username}")
        print()
        print("¡Datos de ejemplo creados exitosamente!")
        print("Puedes usar el usuario de prueba para probar el sistema:")
        print("  Username: testuser")
        print("  Password: testpass123")
        
    except Exception as e:
        print(f"Error al poblar la base de datos: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
