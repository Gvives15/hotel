from ninja import Router, Schema
from typing import Optional
from datetime import date
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Booking
from app.clients.models import Client
from app.rooms.models import Room

router = Router()

# Schemas para la API
class CreateBookingRequest(Schema):
    nombre: str
    email: str
    telefono: Optional[str] = None
    dni: str
    habitacion_id: int
    fecha_inicio: date
    fecha_fin: date
    solicitudes_especiales: Optional[str] = None

class BookingResponse(Schema):
    success: bool
    message: str
    booking_id: Optional[int] = None
    client_id: Optional[int] = None
    total_price: Optional[float] = None

@router.post("/reservas/crear-con-cliente/", response=BookingResponse)
def create_booking_with_client(request, payload: CreateBookingRequest):
    """
    Crea el cliente si no existe y luego la reserva, validando disponibilidad.
    
    Args:
        payload: Datos del cliente y la reserva
    
    Returns:
        Información de la reserva creada
    """
    try:
        with transaction.atomic():
            # Validaciones básicas
            if payload.fecha_inicio >= payload.fecha_fin:
                return {
                    "success": False,
                    "message": "La fecha de inicio debe ser anterior a la fecha de fin",
                    "booking_id": None,
                    "client_id": None,
                    "total_price": None
                }
            
            # Verificar que la habitación existe
            try:
                room = Room.objects.get(id=payload.habitacion_id)
            except Room.DoesNotExist:
                return {
                    "success": False,
                    "message": "La habitación especificada no existe",
                    "booking_id": None,
                    "client_id": None,
                    "total_price": None
                }
            
            # Verificar que la habitación esté disponible
            if not room.available_for_booking:
                return {
                    "success": False,
                    "message": "La habitación no está disponible para reservas",
                    "booking_id": None,
                    "client_id": None,
                    "total_price": None
                }
            
            # Verificar que no haya reservas superpuestas
            conflicting_bookings = Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in_date__lt=payload.fecha_fin,
                check_out_date__gt=payload.fecha_inicio
            )
            
            if conflicting_bookings.exists():
                return {
                    "success": False,
                    "message": "La habitación no está disponible para las fechas solicitadas",
                    "booking_id": None,
                    "client_id": None,
                    "total_price": None
                }
            
            # Buscar o crear el cliente
            client, created = Client.objects.get_or_create(
                email=payload.email,
                defaults={
                    'first_name': payload.nombre.split()[0] if payload.nombre else '',
                    'last_name': ' '.join(payload.nombre.split()[1:]) if len(payload.nombre.split()) > 1 else '',
                    'phone': payload.telefono,
                    'dni': payload.dni,
                }
            )
            
            # Si el cliente ya existía, actualizar datos si es necesario
            if not created:
                if payload.telefono and not client.phone:
                    client.phone = payload.telefono
                if payload.dni and not client.dni:
                    client.dni = payload.dni
                client.save()
            
            # Calcular precio total
            duration = (payload.fecha_fin - payload.fecha_inicio).days
            total_price = room.price * duration
            
            # Crear la reserva
            booking = Booking.objects.create(
                client=client,
                room=room,
                check_in_date=payload.fecha_inicio,
                check_out_date=payload.fecha_fin,
                status='confirmed',  # Estado confirmada como se solicita
                payment_status='pending',
                guests_count=room.capacity,  # Usar capacidad de la habitación
                special_requests=payload.solicitudes_especiales,
                total_price=total_price
            )
            
            # Cambiar estado de la habitación a reservada
            room.change_status('reserved')
            
            return {
                "success": True,
                "message": f"Reserva creada exitosamente. Cliente {'creado' if created else 'encontrado'}.",
                "booking_id": booking.id,
                "client_id": client.id,
                "total_price": float(total_price)
            }
            
    except ValidationError as e:
        return {
            "success": False,
            "message": f"Error de validación: {str(e)}",
            "booking_id": None,
            "client_id": None,
            "total_price": None
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al crear la reserva: {str(e)}",
            "booking_id": None,
            "client_id": None,
            "total_price": None
        } 