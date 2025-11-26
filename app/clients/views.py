from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .models import Client
from app.administration.models import Hotel
from app.bookings.models import Booking

# Vistas existentes
# Create your views here.

@login_required
@require_http_methods(["GET"])
def clients_api(request):
    """API: Listado simple de clientes para el selector del dashboard"""
    qs = Client.objects.all().order_by('first_name', 'last_name')
    hotel_param = request.GET.get('hotel')
    if hotel_param:
        try:
            qs = qs.filter(hotel_id=int(hotel_param))
        except Exception:
            try:
                hotel = Hotel.objects.get(slug=str(hotel_param))
                qs = qs.filter(hotel=hotel)
            except Hotel.DoesNotExist:
                qs = qs.none()
    search = request.GET.get('search')
    if search:
        qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search) | Q(dni__icontains=search))
    data = [
        {
            'id': c.id,
            'full_name': getattr(c, 'full_name', f"{c.first_name} {c.last_name}").strip(),
            'email': c.email,
            'dni': c.dni or ''
        }
        for c in qs
    ]
    return JsonResponse(data, safe=False)

# Endpoint unificado si se desea expandir a POST en futuro
@login_required
@csrf_exempt
@require_http_methods(["GET", "POST"])
def clients_api_collection(request):
    if request.method == "GET":
        return clients_api(request)
    data = {}
    try:
        import json as _json
        data = _json.loads(request.body or "{}")
    except Exception:
        pass
    hotel_param = request.GET.get('hotel') or data.get('hotel') or data.get('hotel_id') or data.get('hotel_slug')
    hotel = None
    if hotel_param:
        try:
            hotel = Hotel.objects.get(id=int(hotel_param))
        except Exception:
            try:
                hotel = Hotel.objects.get(slug=str(hotel_param))
            except Hotel.DoesNotExist:
                hotel = None
    if hotel is None:
        try:
            hotel = Hotel.objects.order_by('id').first()
        except Exception:
            hotel = None
    if hotel is None:
        return JsonResponse({'error': 'Hotel no encontrado'}, status=400)
    c = Client.objects.create(
        first_name=data.get('first_name', '').strip(),
        last_name=data.get('last_name', '').strip(),
        email=data.get('email', '').strip(),
        phone=data.get('phone', '').strip() if data.get('phone') else '',
        dni=data.get('dni', '').strip() if data.get('dni') else '',
        nationality=data.get('nationality', '').strip() if data.get('nationality') else '',
        active=bool(data.get('active', True)),
        vip=bool(data.get('vip', False)),
        hotel=hotel,
    )
    return JsonResponse({'id': c.id, 'message': 'Cliente creado exitosamente'})

@login_required
@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
def clients_api_detail(request, client_id):
    if request.method == "DELETE":
        c = Client.objects.filter(id=client_id).first()
        if not c:
            return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
        if Booking.objects.filter(client=c, status__in=['pending', 'confirmed']).exists():
            return JsonResponse({'error': 'No se puede eliminar cliente con reservas activas'}, status=400)
        c.delete()
        return JsonResponse({'message': 'Cliente eliminado exitosamente'})
    import json as _json
    c = Client.objects.filter(id=client_id).first()
    if not c:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    try:
        data = _json.loads(request.body or "{}")
    except Exception:
        data = {}
    if 'first_name' in data:
        c.first_name = data.get('first_name') or c.first_name
    if 'last_name' in data:
        c.last_name = data.get('last_name') or c.last_name
    if 'email' in data:
        c.email = data.get('email') or c.email
    if 'phone' in data:
        c.phone = data.get('phone') or c.phone
    if 'dni' in data:
        c.dni = data.get('dni') or c.dni
    if 'nationality' in data:
        c.nationality = data.get('nationality') or c.nationality
    if 'active' in data:
        c.active = bool(data.get('active'))
    if 'vip' in data:
        c.vip = bool(data.get('vip'))
    c.save()
    return JsonResponse({'id': c.id, 'message': 'Cliente actualizado exitosamente'})
