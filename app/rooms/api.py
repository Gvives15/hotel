from ninja import Router, Schema
from typing import List, Optional
from datetime import date
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Room
from app.bookings.models import Booking

router = Router()

# Schemas para la API
class RoomSchema(Schema):
    id: int
    number: str
    type: str
    capacity: int
    price: float
    description: Optional[str] = None
    floor: int

class AvailableRoomsResponse(Schema):
    success: bool
    message: str
    rooms: List[RoomSchema]
    total_rooms: int

class AvailableRoomsRequest(Schema):
    fecha_inicio: date
    fecha_fin: date
    personas: int

@router.get("/habitaciones-disponibles/", response=AvailableRoomsResponse)
def get_available_rooms(request, fecha_inicio: date, fecha_fin: date, personas: int):
    """
    Obtiene las habitaciones disponibles entre dos fechas para cierta cantidad de personas.
    
    Args:
        fecha_inicio: Fecha de inicio de la búsqueda
        fecha_fin: Fecha de fin de la búsqueda
        personas: Número de personas para la reserva
    
    Returns:
        Lista de habitaciones disponibles con sus detalles
    """
    try:
        # Validaciones básicas
        if fecha_inicio >= fecha_fin:
            return {
                "success": False,
                "message": "La fecha de inicio debe ser anterior a la fecha de fin",
                "rooms": [],
                "total_rooms": 0
            }
        
        if personas <= 0:
            return {
                "success": False,
                "message": "El número de personas debe ser mayor a 0",
                "rooms": [],
                "total_rooms": 0
            }
        
        # Obtener habitaciones que cumplan los criterios básicos
        available_rooms = Room.objects.filter(
            status='available',  # Solo habitaciones libres
            active=True,         # Solo habitaciones activas
            capacity__gte=personas  # Que tengan capacidad suficiente
        )
        
        # Filtrar habitaciones que no tengan reservas superpuestas
        conflicting_bookings = Booking.objects.filter(
            status__in=['pending', 'confirmed'],  # Solo reservas activas
            check_in_date__lt=fecha_fin,
            check_out_date__gt=fecha_inicio
        ).values_list('room_id', flat=True)
        
        # Excluir habitaciones con reservas conflictivas
        available_rooms = available_rooms.exclude(id__in=conflicting_bookings)
        
        # Preparar respuesta
        rooms_data = []
        for room in available_rooms:
            rooms_data.append({
                "id": room.id,
                "number": room.number,
                "type": room.get_type_display(),
                "capacity": room.capacity,
                "price": float(room.price),
                "description": room.description,
                "floor": room.floor
            })
        
        return {
            "success": True,
            "message": f"Se encontraron {len(rooms_data)} habitaciones disponibles",
            "rooms": rooms_data,
            "total_rooms": len(rooms_data)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al obtener habitaciones disponibles: {str(e)}",
            "rooms": [],
            "total_rooms": 0
        } 