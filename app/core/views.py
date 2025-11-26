from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models.functions import TruncDate
from django.db.models import Count, Q
import json
from django.core.cache import cache
from app.core.services_ia import call_n8n_ia_analyst, IAServiceError, IAServiceNotConfigured
from app.superadmin.services import get_dashboard_data
from django.contrib.auth.forms import UserCreationForm
from app.clients.forms import ClientRegistrationForm
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.http import JsonResponse, HttpResponse
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import locale
from .utils import log_user_action
from app.bookings.views import booking_step1, booking_step2, booking_step3, booking_step4

# Configurar locale para formato de moneda colombiana
try:
    locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Spanish_Colombia.1252')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
        except locale.Error:
            pass  # Usar formato por defecto si no se puede configurar

# Importar modelos de las apps
from app.rooms.models import Room
from app.bookings.models import Booking
from app.clients.models import Client
from app.administration.models import Hotel
from app.administration.models import HotelAdmin, HotelStaff
try:
    from app.cleaning.models import CleaningTask
except ImportError:
    CleaningTask = None

try:
    from app.maintenance.models import MaintenanceRequest
except ImportError:
    MaintenanceRequest = None

def login_view(request):
    """Vista para el login"""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('superadmin_dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)  # Sesión expira al cerrar navegador
            messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
            if user.is_superuser:
                return redirect('superadmin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'login.html')

def register_view(request):
    """Vista para el registro"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            
            # Autenticar al usuario después del registro
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = UserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')

def get_dashboard_metrics(hotel=None):
    """Función para obtener métricas del dashboard de forma optimizada"""
    metrics = {}
    
    # Obtener estadísticas de habitaciones
    try:
        from app.rooms.models import Room as RoomModel
        qs_rooms = RoomModel.objects.all()
        if hotel:
            qs_rooms = qs_rooms.filter(hotel=hotel)
        room_stats = qs_rooms.aggregate(
            total=Count('id'),
            available=Count('id', filter=Q(status='available')),
            cleaning=Count('id', filter=Q(status='cleaning')),
            maintenance=Count('id', filter=Q(status='maintenance'))
        )
        
        # Calcular habitaciones ocupadas basándose en reservas activas
        try:
            from app.bookings.models import Booking as BookingModel
            today = datetime.now().date()
            qs_bookings = BookingModel.objects.all()
            if hotel:
                qs_bookings = qs_bookings.filter(hotel=hotel)
            today = datetime.now().date()
            occupied_rooms = qs_bookings.filter(
                check_in_date__lte=today,
                check_out_date__gte=today,
                status='confirmed'
            ).values('room').distinct().count()
        except ImportError:
            occupied_rooms = RoomModel.objects.filter(status='occupied').count()
        
        metrics.update({
            'total_rooms': room_stats['total'],
            'available_rooms': room_stats['available'],
            'occupied_rooms': occupied_rooms,
            'cleaning_rooms': room_stats['cleaning'],
            'maintenance_rooms': room_stats['maintenance']
        })
    except ImportError:
        # Datos de ejemplo si no hay modelos
        metrics.update({
            'total_rooms': 50,
            'available_rooms': 35,
            'occupied_rooms': 12,
            'cleaning_rooms': 2,
            'maintenance_rooms': 1
        })
    
    # Obtener estadísticas de reservas e ingresos
    try:
        from app.bookings.models import Booking as BookingModel
        today = datetime.now().date()
        start_of_month = datetime.now().replace(day=1).date()
        qs_bookings = BookingModel.objects.all()
        if hotel:
            qs_bookings = qs_bookings.filter(hotel=hotel)
        booking_stats = qs_bookings.aggregate(
            active_bookings=Count('id', filter=Q(
                check_in_date__lte=today,
                check_out_date__gte=today,
                status='confirmed'
            )),
            total_revenue=Sum('total_price', filter=Q(
                check_in_date__gte=start_of_month,
                status__in=['confirmed', 'completed']
            ))
        )
        
        metrics.update({
            'active_bookings': booking_stats['active_bookings'] or 0,
            'total_revenue': booking_stats['total_revenue'] or 0,
            'recent_bookings': qs_bookings.select_related('client', 'room').order_by('-created_at')[:10]
        })
    except ImportError:
        metrics.update({
            'active_bookings': 15,
            'total_revenue': 25000000,
            'recent_bookings': []
        })
    
    # Obtener estadísticas de clientes
    try:
        from app.clients.models import Client as ClientModel
        qs_clients = ClientModel.objects.all()
        if hotel:
            qs_clients = qs_clients.filter(hotel=hotel)
        metrics['total_clients'] = qs_clients.count()
    except ImportError:
        metrics['total_clients'] = 120
    
    # Obtener alertas de mantenimiento
    try:
        from app.maintenance.models import MaintenanceRequest
        qs_m = MaintenanceRequest.objects.select_related('room').filter(status='pending')
        if hotel:
            qs_m = qs_m.filter(room__hotel=hotel)
        metrics['maintenance_alerts'] = qs_m.order_by('-priority', '-created_at')[:5]
    except ImportError:
        metrics['maintenance_alerts'] = []
    
    return metrics


@login_required
def dashboard_metrics_api(request):
    """API endpoint para obtener métricas del dashboard en tiempo real"""
    try:
        metrics = get_dashboard_metrics()
        
        # Formatear datos para JSON
        response_data = {
            'total_rooms': metrics['total_rooms'],
            'available_rooms': metrics['available_rooms'],
            'occupied_rooms': metrics['occupied_rooms'],
            'cleaning_rooms': metrics['cleaning_rooms'],
            'maintenance_rooms': metrics['maintenance_rooms'],
            'total_revenue': float(metrics['total_revenue']),
            'active_bookings': metrics['active_bookings'],
            'total_clients': metrics['total_clients'],
            'timestamp': datetime.now().isoformat()
        }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def dashboard_view(request):
    """Vista del dashboard principal"""
    
    # Registrar acceso al dashboard
    hotel_activo = get_hotel_activo(request)
    log_user_action(request.user, 'dashboard_view', 'Usuario accedió al dashboard', request, hotel_activo)
    
    # Handle quick client creation
    if request.method == 'POST' and request.POST.get('action') == 'create_client':
        try:
            if Client:
                client = Client.objects.create(
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone', ''),
                    dni=request.POST.get('dni'),
                )
                
                # Registrar creación de cliente
                log_user_action(
                    request.user, 
                    'nuevo_cliente', 
                    f'Cliente creado: {client.first_name} {client.last_name}', 
                    request,
                    get_hotel_activo(request)
                )
                
                return JsonResponse({
                    'success': True,
                    'client_name': f"{client.first_name} {client.last_name}",
                    'client_id': client.id
                })
            else:
                return JsonResponse({'success': False, 'error': 'Client model not available'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Usar la función optimizada para obtener métricas
    context = get_dashboard_metrics(hotel_activo)
    
    # Agregar datos adicionales específicos para la vista
    if CleaningTask:
        # Programación de limpieza
        context['cleaning_schedule'] = CleaningTask.objects.select_related('room', 'employee').filter(
            scheduled_date__gte=datetime.now().date()
        ).order_by('scheduled_date')[:10]
    else:
        context['cleaning_schedule'] = []
    
    context['hotel'] = hotel_activo
    return render(request, 'dashboard.html', context)

@login_required
def profile_view(request):
    """Vista del perfil de usuario"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('profile')
    
    return render(request, 'profile.html')

@login_required
def settings_view(request):
    """Vista de configuración"""
    return render(request, 'settings.html')

@login_required
def rooms_view(request):
    """Vista de habitaciones"""
    hotel_activo = get_hotel_activo(request)
    log_user_action(request.user, 'gestionar_habitaciones', 'Usuario accedió a gestión de habitaciones', request, hotel_activo)
    
    if Room:
        base = Room.objects.all()
        rooms = base.filter(hotel=hotel_activo) if hotel_activo else base.none()
    else:
        rooms = []
    return render(request, 'rooms/list.html', {'rooms': rooms, 'hotel': hotel_activo})

@login_required
def bookings_view(request):
    """Vista de reservas"""
    hotel_activo = get_hotel_activo(request)
    log_user_action(request.user, 'nueva_reserva', 'Usuario accedió a gestión de reservas', request, hotel_activo)
    
    if Booking:
        hotel_slug = request.GET.get('hotel')
        qs = Booking.objects.select_related('client', 'room', 'hotel')
        if hotel_slug:
            try:
                hotel = Hotel.objects.get(slug=hotel_slug)
                qs = qs.filter(hotel=hotel)
            except Hotel.DoesNotExist:
                qs = qs.none()
        bookings = qs.all()
    else:
        bookings = []
    return render(request, 'bookings/list.html', {'bookings': bookings, 'hotel': hotel_activo})

@login_required
def clients_view(request):
    """Vista de clientes"""
    if Client:
        hotel_activo = get_hotel_activo(request)
        base = Client.objects.all()
        clients = base.filter(hotel=hotel_activo) if hotel_activo else base.none()
    else:
        clients = []
    return render(request, 'clients/list.html', {'clients': clients, 'hotel': hotel_activo})

@login_required
def cleaning_view(request):
    """Vista de limpieza"""
    hotel_activo = get_hotel_activo(request)
    if CleaningTask:
        tasks = CleaningTask.objects.select_related('room', 'employee').all()
        if hotel_activo:
            tasks = tasks.filter(room__hotel=hotel_activo)
    else:
        tasks = []
    return render(request, 'cleaning/list.html', {'tasks': tasks, 'hotel': hotel_activo})

@login_required
def maintenance_view(request):
    """Vista de mantenimiento"""
    hotel_activo = get_hotel_activo(request)
    if MaintenanceRequest:
        requests = MaintenanceRequest.objects.select_related('room').all()
        if hotel_activo:
            requests = requests.filter(room__hotel=hotel_activo)
    else:
        requests = []
    return render(request, 'maintenance/list.html', {'requests': requests, 'hotel': hotel_activo})

@login_required
def administration_view(request):
    """Vista de administración"""
    hotel_activo = get_hotel_activo(request)
    return render(request, 'administration/dashboard.html', {'hotel': hotel_activo})

@login_required
def reports_view(request):
    """Vista de reportes"""
    hotel_activo = get_hotel_activo(request)
    log_user_action(request.user, 'ver_reportes', 'Usuario accedió a reportes', request, hotel_activo)
    return render(request, 'reports/dashboard.html', {'hotel': hotel_activo})

# ============================================================================
# VISTAS DEL PORTAL DE CLIENTES
# ============================================================================

def client_index_view(request):
    """Vista principal del portal de clientes (pública)"""
    if Room:
        # Habitaciones disponibles para mostrar
        available_rooms = Room.objects.filter(
            status='available',
            active=True
        ).order_by('price')[:6]
        
        # Habitaciones destacadas
        featured_rooms = Room.objects.filter(
            active=True
        ).order_by('?')[:3]  # Aleatorio
    else:
        available_rooms = []
        featured_rooms = []
    
    context = {
        'available_rooms': available_rooms,
        'featured_rooms': featured_rooms,
    }
    
    return render(request, 'client/index.html', context)

def client_index_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse("Hotel no encontrado", status=404)
    if Room:
        base = Room.objects.filter(active=True, hotel=hotel)
        available_rooms = base.filter(status='available').order_by('price')[:6]
        featured_rooms = base.order_by('?')[:3]
    else:
        available_rooms = []
        featured_rooms = []
    tpl_home = 'client/index.html'
    try:
        if getattr(hotel, 'template_id', 'client') == 'nuevo':
            tpl_home = 'diseño-bocking/home.html'
    except Exception:
        pass
    return render(request, tpl_home, {
        'available_rooms': available_rooms,
        'featured_rooms': featured_rooms,
        'hotel': hotel,
    })

def hotel_reserve_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse("Hotel no encontrado", status=404)
    if request.method == 'POST':
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests = request.POST.get('guests')
        try:
            from datetime import datetime
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except Exception:
            return HttpResponse("Fechas inválidas", status=400)
        rooms_qs = Room.objects.filter(hotel=hotel, active=True, status='available')
        try:
            g = int(guests or '1')
            rooms_qs = rooms_qs.filter(capacity__gte=g)
        except Exception:
            pass
        overlapping = Booking.objects.filter(
            room__in=rooms_qs,
            status__in=['confirmed', 'pending'],
            check_in_date__lt=check_out_date,
            check_out_date__gt=check_in_date
        ).values_list('room_id', flat=True)
        available_rooms = rooms_qs.exclude(id__in=list(overlapping))[:30]
        return render(request, 'hotel/reserve_results.html', {
            'hotel': hotel,
            'rooms': available_rooms,
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests,
        })
    return render(request, 'hotel/reserve_search.html', {'hotel': hotel})

def hotel_confirm_reservation_view(request, hotel_slug):
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse("Hotel no encontrado", status=404)
    room_id = request.POST.get('room_id')
    full_name = request.POST.get('full_name')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    document = request.POST.get('document')
    check_in = request.POST.get('check_in')
    check_out = request.POST.get('check_out')
    guests = request.POST.get('guests')
    if not all([room_id, full_name, email, check_in, check_out, guests]):
        return HttpResponse("Faltan datos", status=400)
    try:
        from datetime import datetime
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        room = Room.objects.get(id=room_id, hotel=hotel, active=True)
        parts = full_name.strip().split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
        client, _ = Client.objects.get_or_create(email=email, defaults={
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone or '',
            'dni': document or ''
        })
        client.hotel = hotel
        client.save()
        nights = (check_out_date - check_in_date).days
        total_price = room.price * nights
        booking = Booking.objects.create(
            hotel=hotel,
            client=client,
            room=room,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            guests_count=int(guests),
            total_price=total_price,
            status='pending'
        )
        try:
            from .services import EmailService
            EmailService.send_booking_confirmation(booking.id)
        except Exception:
            pass
        return HttpResponse(f"Reserva creada #{booking.id}")
    except Exception:
        return HttpResponse("Error al crear reserva", status=400)

@login_required
def panel_change_booking_status(request, booking_id):
    if request.method != 'POST':
        return redirect('panel_booking_detail', booking_id=booking_id)
    new_status = request.POST.get('status')
    try:
        hotel_activo = get_hotel_activo(request)
        b = Booking.objects.get(id=booking_id, hotel=hotel_activo)
        if new_status in dict(Booking.STATUS_CHOICES):
            b.status = new_status
            b.save(update_fields=['status'])
            messages.success(request, 'Estado actualizado')
        else:
            messages.error(request, 'Estado inválido')
    except Booking.DoesNotExist:
        messages.error(request, 'Reserva no encontrada')
    return redirect('panel_booking_detail', booking_id=booking_id)

def client_rooms_view(request):
    """Vista de habitaciones disponibles para clientes"""
    if Room:
        # Obtener hotel activo si se proporcionó
        hotel_activo = get_hotel_activo(request)
        # Obtener todas las habitaciones activas por defecto
        base = Room.objects.filter(active=True)
        rooms = base.filter(hotel=hotel_activo) if hotel_activo else base
        
        # Aplicar filtros solo si se proporcionan
        room_type = request.GET.get('type', '').strip()
        min_price = request.GET.get('min_price', '').strip()
        max_price = request.GET.get('max_price', '').strip()
        guests = request.GET.get('guests', '').strip()
        status_filter = request.GET.get('status', '').strip()
        
        # Filtro por tipo de habitación
        if room_type:
            rooms = rooms.filter(type=room_type)
            
        # Filtro por precio mínimo
        if min_price:
            try:
                min_price_val = float(min_price)
                if min_price_val >= 0:
                    rooms = rooms.filter(price__gte=min_price_val)
            except (ValueError, TypeError):
                pass
                
        # Filtro por precio máximo
        if max_price:
            try:
                max_price_val = float(max_price)
                if max_price_val >= 0:
                    rooms = rooms.filter(price__lte=max_price_val)
            except (ValueError, TypeError):
                pass
                
        # Filtro por capacidad de huéspedes
        if guests:
            try:
                guests_val = int(guests)
                if guests_val > 0:
                    rooms = rooms.filter(capacity__gte=guests_val)
            except (ValueError, TypeError):
                pass
                
        # Filtro por estado (opcional). Si no se especifica, mostrar solo disponibles
        if status_filter:
            rooms = rooms.filter(status=status_filter)
        else:
            rooms = rooms.filter(status='available')
            
        # Obtener estadísticas para mostrar
        total_rooms = rooms.count()
        available_rooms = rooms.filter(status='available').count()
        
    else:
        rooms = Room.objects.none()
        total_rooms = 0
        available_rooms = 0
    
    context = {
        'rooms': rooms,
        'room_types': Room.TYPE_CHOICES if Room else [],
        'status_choices': Room.STATUS_CHOICES if Room else [],
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'current_filters': {
            'type': room_type,
            'min_price': min_price,
            'max_price': max_price,
            'guests': guests,
            'status': status_filter,
        },
        'hotel': hotel_activo,
    }
    
    return render(request, 'client/rooms.html', context)

def client_rooms_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse("Hotel no encontrado", status=404)
    if Room:
        rooms = Room.objects.filter(active=True, hotel=hotel)
        room_type = request.GET.get('type', '').strip()
        min_price = request.GET.get('min_price', '').strip()
        max_price = request.GET.get('max_price', '').strip()
        guests = request.GET.get('guests', '').strip()
        status_filter = request.GET.get('status', '').strip()
        if room_type:
            rooms = rooms.filter(type=room_type)
        if min_price:
            try:
                min_price_val = float(min_price)
                if min_price_val >= 0:
                    rooms = rooms.filter(price__gte=min_price_val)
            except Exception:
                pass
        if max_price:
            try:
                max_price_val = float(max_price)
                if max_price_val >= 0:
                    rooms = rooms.filter(price__lte=max_price_val)
            except Exception:
                pass
        if guests:
            try:
                guests_val = int(guests)
                if guests_val > 0:
                    rooms = rooms.filter(capacity__gte=guests_val)
            except Exception:
                pass
        if status_filter:
            rooms = rooms.filter(status=status_filter)
        else:
            rooms = rooms.filter(status='available')
        total_rooms = rooms.count()
        available_rooms = rooms.filter(status='available').count()
    else:
        rooms = Room.objects.none()
        total_rooms = 0
        available_rooms = 0
    return render(request, 'client/rooms.html', {
        'rooms': rooms,
        'room_types': Room.TYPE_CHOICES if Room else [],
        'status_choices': Room.STATUS_CHOICES if Room else [],
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'current_filters': {
            'type': room_type,
            'min_price': min_price,
            'max_price': max_price,
            'guests': guests,
            'status': status_filter,
        },
        'hotel': hotel,
    })

def client_room_detail_view(request, room_id):
    """Vista detallada de una habitación"""
    if Room:
        try:
            room = Room.objects.get(id=room_id, active=True)
        except Room.DoesNotExist:
            messages.error(request, 'Habitación no encontrada.')
            return redirect('client_rooms')
    else:
        room = None
        messages.error(request, 'Sistema de habitaciones no disponible.')
        return redirect('client_rooms')
    
    context = {
        'room': room,
    }
    
    return render(request, 'client/room_detail.html', context)

def client_room_detail_hotel_view(request, hotel_slug, room_id):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        messages.error(request, 'Hotel no encontrado.')
        return redirect('client_index')
    if Room:
        try:
            room = Room.objects.get(id=room_id, hotel=hotel, active=True)
        except Room.DoesNotExist:
            messages.error(request, 'Habitación no encontrada.')
            return redirect('client_rooms_hotel', hotel_slug=hotel_slug)
    else:
        messages.error(request, 'Sistema de habitaciones no disponible.')
        return redirect('client_rooms_hotel', hotel_slug=hotel_slug)
    return render(request, 'client/room_detail.html', {'room': room, 'hotel': hotel})

def client_booking_view(request, room_id=None):
    """Vista para crear una reserva"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para hacer una reserva.')
        return redirect('client_login')
    
    if room_id:
        try:
            room = Room.objects.get(id=room_id, active=True)
            if not room.available_for_booking:
                messages.error(request, 'Esta habitación no está disponible para reservas.')
                return redirect('client_rooms')
        except Room.DoesNotExist:
            messages.error(request, 'Habitación no encontrada.')
            return redirect('client_rooms')
    else:
        room = None
    
    if request.method == 'POST':
        # Procesar la reserva
        room_id_post = request.POST.get('room') or room_id
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests_count = request.POST.get('guests_count')
        special_requests = request.POST.get('special_requests', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        
        if room_id_post and check_in and check_out and guests_count:
            try:
                # Obtener la habitación si no está definida
                if not room:
                    room = Room.objects.get(id=room_id_post, active=True)
                
                # Validar capacidad
                if int(guests_count) > room.capacity:
                    messages.error(request, f'La habitación solo tiene capacidad para {room.capacity} personas.')
                    return render(request, 'client/booking.html', {
                        'room': room,
                        'available_rooms': Room.objects.filter(active=True, status='available'),
                    })
                
                # Validar fechas
                from datetime import datetime
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
                
                if check_in_date >= check_out_date:
                    messages.error(request, 'La fecha de salida debe ser posterior a la fecha de entrada.')
                    return render(request, 'client/booking.html', {
                        'room': room,
                        'available_rooms': Room.objects.filter(active=True, status='available'),
                    })
                
                # Validar que las fechas no sean en el pasado
                from datetime import date
                today = date.today()
                if check_in_date < today:
                    messages.error(request, 'La fecha de entrada no puede ser en el pasado.')
                    return render(request, 'client/booking.html', {
                        'room': room,
                        'available_rooms': Room.objects.filter(active=True, status='available'),
                    })
                
                # Validar disponibilidad de la habitación en las fechas seleccionadas
                overlapping_bookings = Booking.objects.filter(
                    room=room,
                    status__in=['confirmed', 'pending'],
                    check_in_date__lt=check_out_date,
                    check_out_date__gt=check_in_date
                )
                
                if overlapping_bookings.exists():
                    messages.error(request, 'La habitación no está disponible en las fechas seleccionadas. Por favor elige otras fechas.')
                    return render(request, 'client/booking.html', {
                        'room': room,
                        'available_rooms': Room.objects.filter(active=True, status='available'),
                    })
                
                # Obtener o crear el cliente
                if hasattr(request.user, 'client'):
                    client = request.user.client
                    # Actualizar información de contacto si se proporciona
                    if phone:
                        client.phone = phone
                    if email:
                        client.email = email
                    client.save()
                else:
                    # Crear perfil de cliente si no existe
                    import random
                    client_email = email or request.user.email
                    if not client_email or Client.objects.filter(email=client_email).exists():
                        client_email = f'{request.user.username}_{random.randint(1000, 9999)}@hotel.com'
                    
                    client = Client.objects.create(
                        user=request.user,
                        first_name=request.user.first_name or request.user.username,
                        last_name=request.user.last_name or 'Usuario',
                        email=client_email,
                        dni=f'{random.randint(10000000, 99999999)}',
                        phone=phone or f'+54911{random.randint(1000000, 9999999)}'
                    )
                
                # Calcular precio total
                nights = (check_out_date - check_in_date).days
                total_price = room.price * nights
                
                # Crear la reserva
                booking = Booking.objects.create(
                    hotel=room.hotel,
                    client=client,
                    room=room,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    guests_count=int(guests_count),
                    special_requests=special_requests,
                    total_price=total_price,
                    status='confirmed'
                )
                
                # Enviar email de confirmación
                try:
                    from .services import EmailService
                    email_result = EmailService.send_booking_confirmation(booking.id)
                    if email_result.get('success'):
                        messages.success(request, f'¡Reserva #{booking.id} creada exitosamente! Se ha enviado una confirmación a tu email.')
                    else:
                        messages.success(request, f'¡Reserva #{booking.id} creada exitosamente! (El email de confirmación no pudo ser enviado)')
                except Exception as email_error:
                    messages.success(request, f'¡Reserva #{booking.id} creada exitosamente! (Error al enviar email: {str(email_error)})')
                
                return redirect('client_booking_confirmation', booking_id=booking.id)
                    
            except ValidationError as e:
                messages.error(request, f'Error de validación: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error al crear la reserva: {str(e)}')
        else:
            messages.error(request, 'Por favor completa todos los campos requeridos.')
    
    # Obtener fechas mínimas para el formulario
    from datetime import datetime, date, timedelta
    today = date.today()
    min_checkout = today + timedelta(days=1)
    
    context = {
        'room': room,
        'available_rooms': Room.objects.filter(active=True, status='available'),
        'today': today.isoformat(),
        'min_checkout': min_checkout.isoformat(),
    }
    
    return render(request, 'client/booking.html', context)

def client_booking_hotel_view(request, hotel_slug, room_id=None):
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para hacer una reserva.')
        return redirect('client_login_hotel', hotel_slug=hotel_slug)
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if room_id:
        try:
            room = Room.objects.get(id=room_id, hotel=hotel, active=True)
            if not room.available_for_booking:
                messages.error(request, 'Esta habitación no está disponible para reservas.')
                return redirect('client_rooms_hotel', hotel_slug=hotel_slug)
        except Room.DoesNotExist:
            messages.error(request, 'Habitación no encontrada.')
            return redirect('client_rooms_hotel', hotel_slug=hotel_slug)
    else:
        room = None
    if request.method == 'POST':
        room_id_post = request.POST.get('room') or room_id
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests_count = request.POST.get('guests_count')
        special_requests = request.POST.get('special_requests', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        if room_id_post and check_in and check_out and guests_count:
            try:
                if not room:
                    room = Room.objects.get(id=room_id_post, hotel=hotel, active=True)
                if int(guests_count) > room.capacity:
                    messages.error(request, f'La habitación solo tiene capacidad para {room.capacity} personas.')
                    return render(request, 'client/booking.html', {
                        'room': room,
                        'available_rooms': Room.objects.filter(active=True, status='available', hotel=hotel),
                        'hotel': hotel,
                    })
                from datetime import datetime, date
                check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
                if check_in_date >= check_out_date:
                    messages.error(request, 'La fecha de salida debe ser posterior a la fecha de entrada.')
                    return render(request, 'client/booking.html', {
                        'room': room,
                        'available_rooms': Room.objects.filter(active=True, status='available', hotel=hotel),
                        'hotel': hotel,
                    })
                today = date.today()
                if check_in_date < today:
                    messages.error(request, 'La fecha de entrada no puede ser en el pasado.')
                    return render(request, 'client/booking.html', {
                        'room': room,
                        'available_rooms': Room.objects.filter(active=True, status='available', hotel=hotel),
                        'hotel': hotel,
                    })
                if Booking and Client:
                    if hasattr(hotel, 'can_accept_new_bookings') and not hotel.can_accept_new_bookings:
                        messages.error(request, "Este hotel no está aceptando reservas en este momento. Por favor, contacta directamente al establecimiento.")
                        return redirect('client_index_hotel', hotel_slug=hotel.slug)
                    try:
                        client = Client.objects.get(user=request.user)
                    except Client.DoesNotExist:
                        import random
                        client_email = email or request.user.email
                        if not client_email or Client.objects.filter(email=client_email).exists():
                            client_email = f'{request.user.username}_{random.randint(1000, 9999)}@hotel.com'
                        client = Client.objects.create(
                            user=request.user,
                            first_name=request.user.first_name or request.user.username,
                            last_name=request.user.last_name or 'Usuario',
                            email=client_email,
                            dni=f'{random.randint(10000000, 99999999)}',
                            phone=phone or f'+54911{random.randint(1000000, 9999999)}'
                        )
                    nights = (check_out_date - check_in_date).days
                    total_price = room.price * nights
                    booking = Booking.objects.create(
                        hotel=hotel,
                        client=client,
                        room=room,
                        check_in_date=check_in_date,
                        check_out_date=check_out_date,
                        guests_count=int(guests_count),
                        special_requests=special_requests,
                        total_price=total_price,
                        status='confirmed'
                    )
                    try:
                        from .services import EmailService
                        email_result = EmailService.send_booking_confirmation(booking.id)
                        if email_result.get('success'):
                            messages.success(request, f'¡Reserva #{booking.id} creada exitosamente! Se ha enviado una confirmación a tu email.')
                        else:
                            messages.success(request, f'¡Reserva #{booking.id} creada exitosamente! (El email de confirmación no pudo ser enviado)')
                    except Exception:
                        messages.success(request, f'¡Reserva #{booking.id} creada exitosamente!')
                    return redirect('client_booking_confirmation', booking_id=booking.id)
                else:
                    messages.error(request, 'Sistema de reservas no disponible.')
            except ValidationError as e:
                messages.error(request, f'Error de validación: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error al crear la reserva: {str(e)}')
        else:
            messages.error(request, 'Por favor completa todos los campos requeridos.')
    from datetime import date, timedelta
    today = date.today()
    min_checkout = today + timedelta(days=1)
    context = {
        'room': room,
        'available_rooms': Room.objects.filter(active=True, status='available', hotel=hotel),
        'today': today.isoformat(),
        'min_checkout': min_checkout.isoformat(),
        'hotel': hotel,
    }
    return render(request, 'client/booking.html', context)

def booking_step1_hotel_view(request, hotel_slug):
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return booking_step1(request)

def booking_step2_hotel_view(request, hotel_slug):
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return booking_step2(request)

def booking_step3_hotel_view(request, hotel_slug):
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return booking_step3(request)

def booking_step4_hotel_view(request, hotel_slug):
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return booking_step4(request)

def get_room_availability(request, room_id):
    """API para obtener disponibilidad de una habitación por fechas"""
    if not Room:
        return JsonResponse({'error': 'Sistema de habitaciones no disponible'}, status=500)
    
    try:
        room = Room.objects.get(id=room_id, active=True)
    except Room.DoesNotExist:
        return JsonResponse({'error': 'Habitación no encontrada'}, status=404)
    
    # Obtener parámetros de fecha (próximos 60 días por defecto)
    from datetime import date, timedelta
    import json
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    else:
        start_date = date.today()
        end_date = start_date + timedelta(days=60)
    
    # Obtener reservas que afectan este período
    if Booking:
        bookings = Booking.objects.filter(
            room=room,
            status__in=['confirmed', 'pending'],
            check_in_date__lte=end_date,
            check_out_date__gt=start_date
        ).values('check_in_date', 'check_out_date', 'status')
    else:
        bookings = []
    
    # Crear diccionario de disponibilidad
    availability = {}
    current_date = start_date
    
    while current_date <= end_date:
        availability[current_date.isoformat()] = {
            'available': True,
            'status': 'available',
            'price': float(room.price)
        }
        current_date += timedelta(days=1)
    
    # Marcar días ocupados
    for booking in bookings:
        booking_start = booking['check_in_date']
        booking_end = booking['check_out_date']
        
        current_date = max(booking_start, start_date)
        end_booking = min(booking_end, end_date + timedelta(days=1))
        
        while current_date < end_booking:
            if current_date.isoformat() in availability:
                availability[current_date.isoformat()] = {
                    'available': False,
                    'status': 'occupied',
                    'price': float(room.price)
                }
            current_date += timedelta(days=1)
    
    return JsonResponse({
        'room_id': room.id,
        'room_number': room.number,
        'room_type': room.get_type_display(),
        'availability': availability,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    })

def client_booking_confirmation_view(request, booking_id):
    """Vista de confirmación de reserva"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver esta página.')
        return redirect('client_login')
    
    try:
        # Obtener la reserva
        booking = Booking.objects.get(id=booking_id)
        
        # Verificar que la reserva pertenece al usuario actual
        if booking.client.user != request.user:
            messages.error(request, 'No tienes permiso para ver esta reserva.')
            return redirect('client_rooms')
        
        context = {
            'booking': booking,
            'room': booking.room,
            'client': booking.client,
        }
        
        return render(request, 'client/booking_confirmation.html', context)
        
    except Booking.DoesNotExist:
        messages.error(request, 'Reserva no encontrada.')
        return redirect('client_rooms')

def client_my_bookings_view(request):
    """Vista de las reservas del cliente"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver tus reservas.')
        return redirect('client_login')
    
    if Booking and Client:
        # Verificar si el usuario tiene un perfil de cliente
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            # Crear perfil de cliente automáticamente
            import random
            email = request.user.email
            if not email or Client.objects.filter(email=email).exists():
                email = f'{request.user.username}_{random.randint(1000, 9999)}@hotel.com'
            
            client = Client.objects.create(
                user=request.user,
                first_name=request.user.first_name or request.user.username,
                last_name=request.user.last_name or 'Usuario',
                email=email,
                dni=f'{random.randint(10000000, 99999999)}',  # DNI temporal
                phone=f'+54911{random.randint(1000000, 9999999)}'  # Teléfono temporal
            )
            messages.info(request, 'Se ha creado tu perfil de cliente automáticamente.')
        
        # Obtener reservas del cliente actual
        bookings = Booking.objects.filter(
            client=client
        ).select_related('room').order_by('-created_at')
    else:
        bookings = []
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'client/my_bookings.html', context)

def client_my_bookings_hotel_view(request, hotel_slug):
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver tus reservas.')
        return redirect('client_login_hotel', hotel_slug=hotel_slug)
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if Booking and Client:
        try:
            client = Client.objects.get(user=request.user)
        except Client.DoesNotExist:
            return redirect('client_profile_hotel', hotel_slug=hotel_slug)
        bookings = Booking.objects.filter(client=client, hotel=hotel).select_related('room').order_by('-created_at')
    else:
        bookings = []
    return render(request, 'client/my_bookings.html', {'bookings': bookings, 'hotel': hotel})

def client_booking_detail_view(request, booking_id):
    """Vista detallada de una reserva del cliente"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver esta reserva.')
        return redirect('client_login')
    
    if Booking:
        try:
            booking = Booking.objects.get(
                id=booking_id,
                client__user=request.user
            )
        except Booking.DoesNotExist:
            messages.error(request, 'Reserva no encontrada.')
            return redirect('client_my_bookings')
    else:
        booking = None
        messages.error(request, 'Sistema de reservas no disponible.')
        return redirect('client_my_bookings')
    
    context = {
        'booking': booking,
    }
    
    return render(request, 'client/booking_detail.html', context)

def client_booking_detail_hotel_view(request, hotel_slug, booking_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver esta reserva.')
        return redirect('client_login_hotel', hotel_slug=hotel_slug)
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if Booking:
        try:
            booking = Booking.objects.get(id=booking_id, client__user=request.user, hotel=hotel)
        except Booking.DoesNotExist:
            messages.error(request, 'Reserva no encontrada.')
            return redirect('client_my_bookings_hotel', hotel_slug=hotel_slug)
    else:
        messages.error(request, 'Sistema de reservas no disponible.')
        return redirect('client_my_bookings_hotel', hotel_slug=hotel_slug)
    return render(request, 'client/booking_detail.html', {'booking': booking, 'hotel': hotel})

def client_cancel_booking_view(request, booking_id):
    """Vista para cancelar una reserva"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para cancelar una reserva.')
        return redirect('client_login')
    
    if request.method == 'POST':
        if Booking:
            try:
                booking = Booking.objects.get(
                    id=booking_id,
                    client__user=request.user,
                    status__in=['pending', 'confirmed']
                )
                booking.cancel_booking()
                messages.success(request, 'Reserva cancelada exitosamente.')
            except Booking.DoesNotExist:
                messages.error(request, 'Reserva no encontrada o no se puede cancelar.')
        else:
            messages.error(request, 'Sistema de reservas no disponible.')
    
    return redirect('client_my_bookings')

def client_cancel_booking_hotel_view(request, hotel_slug, booking_id):
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para cancelar una reserva.')
        return redirect('client_login_hotel', hotel_slug=hotel_slug)
    if request.method == 'POST' and Booking:
        try:
            hotel = Hotel.objects.get(slug=hotel_slug)
            booking = Booking.objects.get(id=booking_id, client__user=request.user, hotel=hotel, status__in=['pending', 'confirmed'])
            booking.cancel_booking()
            messages.success(request, 'Reserva cancelada exitosamente.')
        except Exception:
            messages.error(request, 'Reserva no encontrada o no se puede cancelar.')
    return redirect('client_my_bookings_hotel', hotel_slug=hotel_slug)

def client_profile_view(request):
    """Vista del perfil del cliente"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver tu perfil.')
        return redirect('client_login')
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Actualizar información del cliente si existe
        if hasattr(request.user, 'client') and Client:
            client = request.user.client
            client.phone = request.POST.get('phone', client.phone)
            client.address = request.POST.get('address', client.address)
            client.nationality = request.POST.get('nationality', client.nationality)
            client.save()
        
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('client_profile')
    
    context = {
        'client': getattr(request.user, 'client', None) if Client else None,
    }
    
    return render(request, 'client/profile.html', context)

def client_profile_hotel_view(request, hotel_slug):
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver tu perfil.')
        return redirect('client_login_hotel', hotel_slug=hotel_slug)
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        if hasattr(request.user, 'client') and Client:
            client = request.user.client
            client.phone = request.POST.get('phone', client.phone)
            client.address = request.POST.get('address', client.address)
            client.nationality = request.POST.get('nationality', client.nationality)
            client.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('client_profile_hotel', hotel_slug=hotel_slug)
    return render(request, 'client/profile.html', {'client': getattr(request.user, 'client', None) if Client else None, 'hotel': hotel})

def client_login_view(request):
    """Vista de login para clientes"""
    if request.user.is_authenticated:
        return redirect('client_index')
    
    # Obtener el username del parámetro GET si viene del registro
    username_from_register = request.GET.get('username', '')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            is_client = hasattr(user, 'client') and getattr(user, 'client') is not None
            if not is_client:
                messages.error(request, 'Solo los clientes pueden iniciar sesión en el portal.')
            else:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0)
                messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
                return redirect('client_index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'client/login.html', {'username_from_register': username_from_register})

def client_login_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if request.user.is_authenticated:
        return redirect('client_index_hotel', hotel_slug=hotel_slug)
    username_from_register = request.GET.get('username', '')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            is_client = hasattr(user, 'client') and getattr(user, 'client') is not None
            if not is_client:
                messages.error(request, 'Solo los clientes pueden iniciar sesión en el portal.')
            else:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0)
                messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
                return redirect('client_index_hotel', hotel_slug=hotel_slug)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'client/login.html', {'username_from_register': username_from_register, 'hotel': hotel})

def client_register_view(request):
    """Vista de registro para clientes con validaciones mejoradas"""
    if request.user.is_authenticated:
        return redirect('client_index')
    
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # El cliente se creará automáticamente mediante las señales
            # Actualizar campos adicionales si se proporcionaron
            try:
                # Esperar a que las señales creen el cliente
                from django.db import transaction
                transaction.on_commit(lambda: update_client_additional_fields(user, form.cleaned_data))
            except Exception as e:
                # Si hay error, continuar sin los campos adicionales
                pass
            
            # En lugar de hacer login automático, redirigir al login con el username
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión con tus credenciales.')
            # Redirigir al login con el username como parámetro
            return redirect(f'/portal/login/?username={user.username}')
        else:
            # Los errores se mostrarán automáticamente en el template
            pass
    else:
        form = ClientRegistrationForm()
    
    return render(request, 'client/register.html', {'form': form})

def client_register_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if request.user.is_authenticated:
        return redirect('client_index_hotel', hotel_slug=hotel_slug)
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            try:
                from django.db import transaction
                transaction.on_commit(lambda: update_client_additional_fields(user, form.cleaned_data))
            except Exception:
                pass
            messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión con tus credenciales.')
            return redirect(f'/h/{hotel_slug}/portal/login/?username={user.username}')
    else:
        form = ClientRegistrationForm()
    return render(request, 'client/register.html', {'form': form, 'hotel': hotel})

def client_logout_view(request):
    """Vista para cerrar sesión de clientes"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('client_index')

def client_logout_hotel_view(request, hotel_slug):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('client_index_hotel', hotel_slug=hotel_slug)

def update_client_additional_fields(user, form_data):
    """Función auxiliar para actualizar campos adicionales del cliente"""
    try:
        if hasattr(user, 'client'):
            client = user.client
            if form_data.get('phone'):
                client.phone = form_data.get('phone')
            if form_data.get('address'):
                client.address = form_data.get('address')
            if form_data.get('nationality'):
                client.nationality = form_data.get('nationality')
            client.save()
    except Exception:
        pass  # Ignorar errores silenciosamente


def client_simulate_payment_view(request, booking_id):
    """Simula el pago de una reserva desde el portal del cliente."""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para realizar pagos.')
        return redirect('client_login')

    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('client_booking_detail', booking_id=booking_id)

    try:
        from django.db import transaction
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(
                id=booking_id,
                client__user=request.user
            )

            if booking.status not in ['pending', 'confirmed']:
                messages.error(request, 'La reserva no está en estado válido para pago.')
                return redirect('client_booking_detail', booking_id=booking_id)

            # Simulación de pago con soporte de monto parcial
            result = request.POST.get('result', 'success')
            from decimal import Decimal, InvalidOperation

            if result == 'partial':
                amount_str = request.POST.get('amount')
                if not amount_str:
                    messages.error(request, 'Debes ingresar un monto para el pago parcial.')
                    return redirect('client_booking_detail', booking_id=booking_id)
                try:
                    amount = Decimal(amount_str)
                except (InvalidOperation, TypeError):
                    messages.error(request, 'Monto inválido para pago parcial.')
                    return redirect('client_booking_detail', booking_id=booking_id)
                if amount <= Decimal('0'):
                    messages.error(request, 'El monto debe ser mayor a 0.')
                    return redirect('client_booking_detail', booking_id=booking_id)

                # Acumular pagos parciales
                current_paid = booking.paid_amount or Decimal('0')
                new_paid = current_paid + amount

                # Determinar estado según total
                total = booking.total_price or Decimal('0')
                if new_paid >= total:
                    booking.payment_status = 'paid'
                    booking.paid_amount = total
                else:
                    booking.payment_status = 'partial'
                    booking.paid_amount = new_paid

            else:
                # Pago exitoso total
                booking.payment_status = 'paid'
                booking.paid_amount = booking.total_price

            booking.save()

        # Enviar email de confirmación/recibo de pago
        try:
            from .services import EmailService
            EmailService.send_payment_confirmation(booking.id)
        except Exception:
            import logging
            logging.getLogger(__name__).warning(f"Fallo el envío de email de pago para reserva {booking.id}")

        messages.success(request, 'Pago simulado procesado correctamente.')
        return redirect('client_booking_detail', booking_id=booking_id)

    except Booking.DoesNotExist:
        messages.error(request, 'Reserva no encontrada.')
        return redirect('client_my_bookings')
    except Exception:
        messages.error(request, 'Ocurrió un error al procesar el pago simulado.')
        return redirect('client_booking_detail', booking_id=booking_id)

# --- PDF de Reserva (Cliente) ---
@login_required
def client_booking_pdf_view(request, booking_id):
    """Genera y descarga un PDF simple con los datos de la reserva del cliente."""
    # Restringir a que el usuario sea dueño de la reserva (si no es staff)
    try:
        if request.user.is_staff:
            booking = Booking.objects.get(id=booking_id)
        else:
            booking = Booking.objects.get(id=booking_id, client__user=request.user)
    except Booking.DoesNotExist:
        messages.error(request, 'Reserva no encontrada.')
        return redirect('client_my_bookings')

    # Generar PDF con ReportLab
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reserva_{booking.id}.pdf"'

        c = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        # Encabezado
        c.setFont("Helvetica-Bold", 16)
        c.drawString(20*mm, height - 25*mm, "O11CE Hotel - Detalle de Reserva")
        c.setFont("Helvetica", 10)
        c.drawString(20*mm, height - 32*mm, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Datos de reserva
        y = height - 50*mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20*mm, y, f"Reserva #{booking.id}")
        y -= 8*mm
        c.setFont("Helvetica", 11)
        c.drawString(20*mm, y, f"Habitación: {booking.room.get_type_display} (N° {booking.room.number})")
        y -= 7*mm
        c.drawString(20*mm, y, f"Check-in: {booking.check_in_date.strftime('%d/%m/%Y')}  -  Check-out: {booking.check_out_date.strftime('%d/%m/%Y')}")
        y -= 7*mm
        c.drawString(20*mm, y, f"Duración: {booking.duration} noche(s)")
        y -= 7*mm
        c.drawString(20*mm, y, f"Huéspedes: {booking.guests_count}")
        y -= 7*mm
        c.drawString(20*mm, y, f"Estado: {booking.status}")
        y -= 7*mm
        c.drawString(20*mm, y, f"Pago: {booking.payment_status}")
        y -= 7*mm
        c.drawString(20*mm, y, f"Total: ${booking.total_price}")
        
        # Solicitudes especiales
        if booking.special_requests:
            y -= 12*mm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20*mm, y, "Solicitudes Especiales:")
            y -= 7*mm
            c.setFont("Helvetica", 10)
            # Partir texto si es largo
            import textwrap
            for line in textwrap.wrap(booking.special_requests, width=80):
                c.drawString(20*mm, y, line)
                y -= 6*mm

        # Pie de página
        c.setFont("Helvetica", 9)
        c.drawString(20*mm, 15*mm, "Gracias por elegir O11CE Hotel. Tel: +1234567890 | soporte@o11ce.com")

        c.showPage()
        c.save()
        return response
    except Exception:
        messages.error(request, 'No se pudo generar el PDF. Contacta soporte.')
        return redirect('client_booking_detail', booking_id=booking_id)
def is_superadmin(user):
    from django.conf import settings
    return (
        getattr(user, 'is_superuser', False)
        or user.groups.filter(name='superadmin').exists()
        or (getattr(settings, 'DEBUG', False) and getattr(user, 'is_authenticated', False))
    )

def is_hotel_admin(user, hotel):
    try:
        return HotelAdmin.objects.filter(user=user, hotel=hotel).exists()
    except Exception:
        return False

def is_hotel_staff(user, hotel):
    try:
        return HotelStaff.objects.filter(user=user, hotel=hotel).exists()
    except Exception:
        return False

@login_required
def superadmin_dashboard_view(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from django.utils import timezone
    today = timezone.now().date()
    hotels = Hotel.objects.all().order_by('name')
    total_rooms = 0
    occupied_rooms = 0
    total_reservas_hoy = 0
    pendientes_hoy = 0
    confirmadas_hoy = 0
    from app.rooms.models import Room
    from app.bookings.models import Booking
    for h in hotels:
        total_rooms += Room.objects.filter(hotel=h).count()
        ocupadas = Booking.objects.filter(hotel=h, status='confirmed', check_in_date__lte=today, check_out_date__gte=today).values('room').distinct().count()
        occupied_rooms += ocupadas
        reservas_hoy = Booking.objects.filter(hotel=h, check_in_date__lte=today, check_out_date__gte=today).count()
        total_reservas_hoy += reservas_hoy
        pendientes_hoy += Booking.objects.filter(hotel=h, status='pending', check_in_date__lte=today, check_out_date__gte=today).count()
        confirmadas_hoy += Booking.objects.filter(hotel=h, status='confirmed', check_in_date__lte=today, check_out_date__gte=today).count()
    ocupacion = 0
    if total_rooms > 0:
        from decimal import Decimal
        ocupacion = round((Decimal(occupied_rooms) / Decimal(total_rooms)) * Decimal('100'), 2)
    context = {
        'hotels': hotels,
        'total_rooms': total_rooms,
        'occupied_rooms': occupied_rooms,
        'total_reservas_hoy': total_reservas_hoy,
        'pendientes_hoy': pendientes_hoy,
        'confirmadas_hoy': confirmadas_hoy,
        'ocupacion_percent': ocupacion,
    }
    return render(request, 'superadmin/dashboard.html', context)
def _parse_date_params(request):
    try:
        to_str = request.GET.get('hasta')
        from_str = request.GET.get('desde')
        days = int(request.GET.get('days') or '30')
        if days > 90:
            return None, None, None
        today = timezone.now().date()
        to_date = today if not to_str else timezone.datetime.strptime(to_str, '%Y-%m-%d').date()
        from_date = (to_date - timezone.timedelta(days=30)) if not from_str else timezone.datetime.strptime(from_str, '%Y-%m-%d').date()
        return from_date, to_date, days
    except Exception:
        return None, None, None
def _kpis_for_hotel(hotel):
    today = timezone.now().date()
    from app.rooms.models import Room
    total_rooms = Room.objects.filter(hotel=hotel).count()
    occupied_rooms = Booking.objects.filter(hotel=hotel, status='confirmed', check_in_date__lte=today, check_out_date__gt=today).values('room_id').distinct().count()
    occupancy_today = None if total_rooms == 0 else round(occupied_rooms / total_rooms, 4)
    bookings_checkin_today_total = Booking.objects.filter(hotel=hotel, check_in_date=today).count()
    return occupancy_today, bookings_checkin_today_total
def _kpis_for_global():
    today = timezone.now().date()
    from app.rooms.models import Room
    total_rooms = Room.objects.count()
    occupied_rooms = Booking.objects.filter(status='confirmed', check_in_date__lte=today, check_out_date__gt=today).values('room_id').distinct().count()
    occupancy_today = None if total_rooms == 0 else round(occupied_rooms / total_rooms, 4)
    bookings_checkin_today_total = Booking.objects.filter(check_in_date=today).count()
    return occupancy_today, bookings_checkin_today_total
def _series_daily_bookings(from_date, to_date, hotel=None):
    base = Booking.objects.filter(check_in_date__gte=from_date, check_in_date__lte=to_date)
    if hotel:
        base = base.filter(hotel=hotel)
    arr = []
    cur = from_date
    while cur <= to_date:
        day = base.filter(check_in_date=cur)
        arr.append({
            'date': cur.strftime('%Y-%m-%d'),
            'pending': day.filter(status='pending').count(),
            'confirmed': day.filter(status='confirmed').count(),
            'cancelled': day.filter(status='cancelled').count(),
        })
        cur += timezone.timedelta(days=1)
    return arr
def _distribution_status(from_date, to_date, hotel=None):
    qs = Booking.objects.filter(check_in_date__gte=from_date, check_in_date__lte=to_date)
    if hotel:
        qs = qs.filter(hotel=hotel)
    agg = qs.aggregate(
        pending=Count('id', filter=Q(status='pending')),
        confirmed=Count('id', filter=Q(status='confirmed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )
    return {'pending': agg.get('pending') or 0, 'confirmed': agg.get('confirmed') or 0, 'cancelled': agg.get('cancelled') or 0}
@login_required
def superadmin_api_dashboard_hotel(request, hotel_id):
    if not is_superadmin(request.user):
        return JsonResponse({'error': 'forbidden'}, status=403)
    from_date, to_date, days = _parse_date_params(request)
    if from_date is None:
        return JsonResponse({'error': 'invalid_params'}, status=400)
    try:
        hotel = Hotel.objects.get(id=hotel_id)
    except Hotel.DoesNotExist:
        return JsonResponse({'error': 'hotel_not_found'}, status=404)
    occupancy_today, bookings_today = _kpis_for_hotel(hotel)
    reservations_period_count = Booking.objects.filter(hotel=hotel, check_in_date__gte=from_date, check_in_date__lte=to_date).count()
    series = _series_daily_bookings(from_date, to_date, hotel)
    dist = _distribution_status(from_date, to_date, hotel)
    resp = {
        'meta': {
            'version': 1,
            'scope': 'hotel',
            'hotel_id': hotel.id,
            'hotel_name': hotel.name,
            'date_range': {'from': from_date.strftime('%Y-%m-%d'), 'to': to_date.strftime('%Y-%m-%d')}
        },
        'kpis': {
            'occupancy_today': occupancy_today,
            'bookings_checkin_today_total': bookings_today,
            'reservations_period_count': reservations_period_count
        },
        'series': {
            'daily_bookings': series
        },
        'distributions': {
            'status': dist
        }
    }
    return JsonResponse(resp)
@login_required
def superadmin_api_dashboard_global(request):
    if not is_superadmin(request.user):
        return JsonResponse({'error': 'forbidden'}, status=403)
    from_date, to_date, days = _parse_date_params(request)
    if from_date is None:
        return JsonResponse({'error': 'invalid_params'}, status=400)
    occupancy_today, bookings_today = _kpis_for_global()
    reservations_period_count = Booking.objects.filter(check_in_date__gte=from_date, check_in_date__lte=to_date).count()
    series = _series_daily_bookings(from_date, to_date, None)
    dist = _distribution_status(from_date, to_date, None)
    resp = {
        'meta': {
            'version': 1,
            'scope': 'global',
            'date_range': {'from': from_date.strftime('%Y-%m-%d'), 'to': to_date.strftime('%Y-%m-%d')}
        },
        'kpis': {
            'occupancy_today': occupancy_today,
            'bookings_checkin_today_total': bookings_today,
            'reservations_period_count': reservations_period_count
        },
        'series': {
            'daily_bookings': series
        },
        'distributions': {
            'status': dist
        }
    }
    return JsonResponse(resp)
@login_required
def superadmin_api_ia_analisis(request):
    if not is_superadmin(request.user):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    key = f"ia_analisis_superadmin:{request.user.id}"
    if cache.get(key):
        return JsonResponse({'error': 'too_many_requests'}, status=429)
    cache.set(key, True, 15)
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid_json'}, status=400)
    scope = body.get('scope')
    hotel_id = body.get('hotel_id')
    desde_str = body.get('desde')
    hasta_str = body.get('hasta')
    question = body.get('question') or 'Analizá la situación actual y decime qué revisar primero.'
    if scope not in ['global', 'hotel']:
        return JsonResponse({'error': 'invalid_scope'}, status=400)
    try:
        desde = timezone.datetime.strptime(desde_str, '%Y-%m-%d').date()
        hasta = timezone.datetime.strptime(hasta_str, '%Y-%m-%d').date()
    except Exception:
        return JsonResponse({'error': 'invalid_dates'}, status=400)
    if desde > hasta:
        return JsonResponse({'error': 'invalid_dates'}, status=400)
    hotel = None
    hotel_name = None
    if scope == 'hotel':
        if not hotel_id:
            return JsonResponse({'error': 'hotel_id_required'}, status=400)
        try:
            hotel = Hotel.objects.get(id=hotel_id)
            hotel_name = hotel.name
        except Hotel.DoesNotExist:
            return JsonResponse({'error': 'hotel_not_found'}, status=404)
    try:
        dashboard_data = get_dashboard_data(scope=scope, hotel=hotel, desde=desde, hasta=hasta)
    except Exception:
        return JsonResponse({'error': 'dashboard_data_error'}, status=500)
    kpis = dashboard_data.get('kpis', {})
    series = dashboard_data.get('series', {})
    distributions = dashboard_data.get('distributions', {})
    payload = {
        'meta': {
            'version': 1,
            'scope': scope,
            'hotel_name': hotel_name,
            'date_range': {'from': desde_str, 'to': hasta_str}
        },
        'kpis': {
            'occupancy_today': kpis.get('occupancy_today'),
            'bookings_checkin_today_total': kpis.get('bookings_checkin_today_total', 0),
            'reservations_period_count': kpis.get('reservations_period_count', 0)
        },
        'series': {
            'daily_bookings': series.get('daily_bookings', [])
        },
        'distributions': {
            'status': distributions.get('status', {'pending': 0, 'confirmed': 0, 'cancelled': 0})
        },
        'question': question
    }
    try:
        ia_result = call_n8n_ia_analyst(payload)
        try:
            from app.core.models import ActionLog
            ActionLog.objects.create(
                user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
                action='superadmin_ia_analisis',
                description=f"scope={scope}, hotel_id={getattr(hotel, 'id', None)}, status=200",
                hotel=hotel
            )
        except Exception:
            pass
        return JsonResponse(ia_result, status=200)
    except IAServiceNotConfigured:
        try:
            from app.core.models import ActionLog
            ActionLog.objects.create(
                user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
                action='superadmin_ia_analisis',
                description=f"scope={scope}, hotel_id={getattr(hotel, 'id', None)}, status=503(ia_not_configured)",
                hotel=hotel
            )
        except Exception:
            pass
        return JsonResponse({'error': 'ia_not_configured'}, status=503)
    except IAServiceError as e:
        try:
            from app.core.models import ActionLog
            ActionLog.objects.create(
                user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
                action='superadmin_ia_analisis',
                description=f"scope={scope}, hotel_id={getattr(hotel, 'id', None)}, status=503(ia_error)",
                hotel=hotel
            )
        except Exception:
            pass
        return JsonResponse({'error': 'ia_error', 'detail': str(e)}, status=503)

@login_required
def superadmin_api_ia_chat(request):
    if not is_superadmin(request.user):
        return JsonResponse({'error': 'forbidden'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'method_not_allowed'}, status=405)
    key = f"ia_chat_superadmin:{request.user.id}"
    if cache.get(key):
        return JsonResponse({'error': 'too_many_requests'}, status=429)
    cache.set(key, True, 15)
    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid_json'}, status=400)
    scope = body.get('scope')
    hotel_id = body.get('hotel_id')
    desde_str = body.get('desde')
    hasta_str = body.get('hasta')
    question = (body.get('question') or '').strip()
    if not question:
        question = 'Analiza el contexto y sugiere acciones prioritarias.'
    if scope not in ['global', 'hotel']:
        return JsonResponse({'error': 'invalid_scope'}, status=400)
    try:
        desde = timezone.datetime.strptime(desde_str, '%Y-%m-%d').date()
        hasta = timezone.datetime.strptime(hasta_str, '%Y-%m-%d').date()
    except Exception:
        return JsonResponse({'error': 'invalid_dates'}, status=400)
    if desde > hasta:
        return JsonResponse({'error': 'invalid_dates'}, status=400)
    hotel = None
    hotel_name = None
    if scope == 'hotel':
        if not hotel_id:
            return JsonResponse({'error': 'hotel_id_required'}, status=400)
        try:
            hotel = Hotel.objects.get(id=hotel_id)
            hotel_name = hotel.name
        except Hotel.DoesNotExist:
            return JsonResponse({'error': 'hotel_not_found'}, status=404)
    try:
        dashboard_data = get_dashboard_data(scope=scope, hotel=hotel, desde=desde, hasta=hasta)
    except Exception:
        return JsonResponse({'error': 'dashboard_data_error'}, status=500)
    kpis = dashboard_data.get('kpis', {})
    series = dashboard_data.get('series', {})
    distributions = dashboard_data.get('distributions', {})
    payload = {
        'meta': {
            'version': 1,
            'scope': scope,
            'hotel_name': hotel_name,
            'date_range': {'from': desde_str, 'to': hasta_str}
        },
        'kpis': {
            'occupancy_today': kpis.get('occupancy_today'),
            'bookings_checkin_today_total': kpis.get('bookings_checkin_today_total', 0),
            'reservations_period_count': kpis.get('reservations_period_count', 0)
        },
        'series': {
            'daily_bookings': series.get('daily_bookings', [])
        },
        'distributions': {
            'status': distributions.get('status', {'pending': 0, 'confirmed': 0, 'cancelled': 0})
        },
        'question': question
    }
    try:
        ia_result = call_n8n_ia_analyst(payload)
        try:
            from app.core.models import ActionLog
            ActionLog.objects.create(
                user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
                action='superadmin_ia_analisis',
                description=f"scope={scope}, hotel_id={hotel_id}, status=200",
                hotel=hotel
            )
        except Exception:
            pass
        return JsonResponse(ia_result, status=200)
    except IAServiceNotConfigured:
        try:
            from app.core.models import ActionLog
            ActionLog.objects.create(
                user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
                action='superadmin_ia_analisis',
                description=f"scope={scope}, hotel_id={hotel_id}, status=503(ia_not_configured)",
                hotel=hotel
            )
        except Exception:
            pass
        return JsonResponse({'error': 'ia_not_configured'}, status=503)
    except IAServiceError:
        try:
            from app.core.models import ActionLog
            ActionLog.objects.create(
                user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
                action='superadmin_ia_analisis',
                description=f"scope={scope}, hotel_id={hotel_id}, status=503(ia_error)",
                hotel=hotel
            )
        except Exception:
            pass
        return JsonResponse({'error': 'IA no disponible en este momento'}, status=503)

@login_required
def superadmin_api_hotels(request):
    if not is_superadmin(request.user):
        return JsonResponse({'error': 'forbidden'}, status=403)
    items = list(Hotel.objects.all().order_by('name').values('id', 'name', 'slug', 'is_blocked'))
    return JsonResponse({'hotels': items})

@login_required
def superadmin_hotels_list_view(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    hotels = Hotel.objects.all().order_by('name')
    return render(request, 'superadmin/hotels_list.html', {'hotels': hotels})

@login_required
def superadmin_hotel_detail_view(request, hotel_id):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from django.shortcuts import get_object_or_404
    hotel = get_object_or_404(Hotel, id=hotel_id)
    try:
        from app.rooms.models import Room as RModel
        from app.bookings.models import Booking as BModel
        today = timezone.now().date()
        rooms_qs = RModel.objects.filter(hotel=hotel)
        total_rooms = rooms_qs.count()
        cleaning_rooms = rooms_qs.filter(status='cleaning').count()
        maintenance_rooms = rooms_qs.filter(status='maintenance').count()
        reserved_rooms = rooms_qs.filter(status='reserved').count()
        available_rooms = rooms_qs.filter(status='available').count()
        occupied_distinct = BModel.objects.filter(hotel=hotel, status='confirmed', check_in_date__lte=today, check_out_date__gte=today).values('room').distinct().count()
        rooms_list = []
        recent_bookings_map = {}
        recent = list(BModel.objects.filter(hotel=hotel).select_related('room', 'client').order_by('-created_at')[:200])
        for b in recent:
            k = getattr(b.room, 'id', None)
            if k is None:
                continue
            arr = recent_bookings_map.get(k) or []
            if len(arr) < 3:
                arr.append({'id': b.id, 'check_in': str(getattr(b, 'check_in_date', '')), 'check_out': str(getattr(b, 'check_out_date', '')), 'status': b.status})
            recent_bookings_map[k] = arr
        for r in rooms_qs.order_by('number')[:200]:
            rooms_list.append({
                'id': r.id,
                'number': r.number,
                'type': r.type,
                'capacity': r.capacity,
                'price': float(r.price),
                'status': r.status,
                'recent': recent_bookings_map.get(r.id, []),
            })
        import json
        context = {
            'hotel': hotel,
            'rooms': rooms_list,
            'rooms_labels': json.dumps(['Disponibles', 'Ocupadas', 'Limpieza', 'Mantenimiento', 'Reservadas']),
            'rooms_counts': json.dumps([available_rooms, occupied_distinct, cleaning_rooms, maintenance_rooms, reserved_rooms]),
            'total_rooms': total_rooms,
        }
    except Exception:
        context = {'hotel': hotel, 'rooms': [], 'rooms_labels': '[]', 'rooms_counts': '[]', 'total_rooms': 0}
    return render(request, 'superadmin/hotel_detail.html', context)

@login_required
def superadmin_block_hotel(request, hotel_id):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from django.shortcuts import get_object_or_404
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.method == 'POST':
        hotel.is_blocked = True
        hotel.save(update_fields=['is_blocked'])
        messages.success(request, 'Hotel bloqueado')
    return redirect('superadmin_hotel_detail', hotel_id=hotel.id)

@login_required
def superadmin_unblock_hotel(request, hotel_id):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from django.shortcuts import get_object_or_404
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.method == 'POST':
        hotel.is_blocked = False
        hotel.save(update_fields=['is_blocked'])
        messages.success(request, 'Hotel desbloqueado')
    return redirect('superadmin_hotel_detail', hotel_id=hotel.id)

@login_required
def superadmin_audit_actions_view(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from app.core.models import ActionLog
    from django.db.models.functions import TruncDate
    qs = ActionLog.objects.select_related('user', 'hotel').order_by('-created_at')
    dist = list(qs.values('action').annotate(total=Count('id')).order_by('-total'))
    daily = list(qs.annotate(date=TruncDate('created_at')).values('date', 'action').annotate(total=Count('id')).order_by('date'))
    top_users = list(qs.values('user__username').annotate(total=Count('id')).order_by('-total')[:10])
    hotels = Hotel.objects.all().order_by('name')
    hotels_labels = []
    hotels_totals = []
    for h in hotels:
        hotels_labels.append(h.name)
        hotels_totals.append(qs.filter(hotel=h).count())
    # Datos robustos desde otras tablas
    try:
        from app.bookings.models import Booking as BModel
        bookings_per_hotel = list(BModel.objects.values('hotel__name').annotate(total=Count('id')).order_by('-total'))
    except Exception:
        bookings_per_hotel = []
    try:
        from app.core.models import EmailLog as EModel
        emails_qs = EModel.objects.all()
        emails_per_hotel = list(
            emails_qs.values('booking__hotel__name').annotate(total=Count('id')).order_by('-total')
        )
    except Exception:
        emails_per_hotel = []
    import json
    context = {
        'distribution': json.dumps(dist, default=str),
        'daily_series': json.dumps(daily, default=str),
        'top_users': json.dumps(top_users, default=str),
        'hotels_labels': json.dumps(hotels_labels, default=str),
        'hotels_totals': json.dumps(hotels_totals, default=str),
        'bookings_per_hotel': json.dumps(bookings_per_hotel, default=str),
        'emails_per_hotel': json.dumps(emails_per_hotel, default=str),
    }
    return render(request, 'superadmin/audit_actions.html', context)

@login_required
def superadmin_audit_emails_view(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from app.core.models import EmailLog
    hotel_id = request.GET.get('hotel')
    qs = EmailLog.objects.order_by('-created_at')
    if hotel_id:
        try:
            h = Hotel.objects.get(id=hotel_id)
            qs = qs.filter(content__icontains=h.name)
        except Hotel.DoesNotExist:
            qs = qs.none()
    return render(request, 'superadmin/audit_emails.html', {'emails': qs})

@login_required
def superadmin_users_list_view(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from django.contrib.auth.models import Group
    search = request.GET.get('search', '').strip()
    hotel_param = request.GET.get('hotel')
    hotels = Hotel.objects.all().order_by('name')
    hotel_selected = None
    if hotel_param:
        try:
            hotel_selected = Hotel.objects.get(id=int(hotel_param))
        except Exception:
            try:
                hotel_selected = Hotel.objects.get(slug=str(hotel_param))
            except Hotel.DoesNotExist:
                hotel_selected = None
    qs_users = get_user_model().objects.exclude(client__isnull=False)
    if search:
        qs_users = qs_users.filter(Q(username__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search))
    users = qs_users.order_by('username')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        hotel_param = request.POST.get('hotel')
        try:
            u = get_user_model().objects.get(id=user_id)
            hotel = None
            if hotel_param:
                try:
                    hotel = Hotel.objects.get(id=int(hotel_param))
                except Exception:
                    try:
                        hotel = Hotel.objects.get(slug=str(hotel_param))
                    except Hotel.DoesNotExist:
                        hotel = None
            if role == 'hotel_admin':
                if hotel:
                    HotelAdmin.objects.update_or_create(hotel=hotel, defaults={'user': u})
                    u.is_staff = True
                    u.save(update_fields=['is_staff'])
                    messages.success(request, 'Admin de hotel asignado')
                else:
                    messages.error(request, 'Hotel inválido')
            elif role == 'hotel_staff':
                if hotel:
                    from app.administration.models import HotelStaff
                    HotelStaff.objects.update_or_create(hotel=hotel, user=u, defaults={})
                    messages.success(request, 'Staff de hotel asignado')
                else:
                    messages.error(request, 'Hotel inválido')
            elif role == 'remove_hotel_admin':
                from app.administration.models import HotelAdmin as HAdmin
                qs = HAdmin.objects.filter(user=u)
                if hotel:
                    qs = qs.filter(hotel=hotel)
                count, _ = qs.delete()
                messages.success(request, f'Removido admin ({count})')
            elif role == 'remove_hotel_staff':
                from app.administration.models import HotelStaff
                qs = HotelStaff.objects.filter(user=u)
                if hotel:
                    qs = qs.filter(hotel=hotel)
                count, _ = qs.delete()
                messages.success(request, f'Removido staff ({count})')
            else:
                g, _ = Group.objects.get_or_create(name=role)
                u.groups.add(g)
                messages.success(request, 'Rol asignado')
        except Exception:
            messages.error(request, 'No se pudo asignar el rol')
        return redirect('superadmin_users')
    from app.administration.models import HotelAdmin as HAdmin
    from app.administration.models import HotelStaff as HStaff
    if hotel_selected:
        admin_ids = list(HAdmin.objects.filter(hotel=hotel_selected).values_list('user_id', flat=True))
        staff_ids = list(HStaff.objects.filter(hotel=hotel_selected).values_list('user_id', flat=True))
        ids = set(admin_ids) | set(staff_ids)
        users = users.filter(id__in=ids)
    hotels_roles = []
    roles_chart_labels = []
    roles_chart_admins = []
    roles_chart_staff = []
    for h in hotels:
        admins = list(HAdmin.objects.select_related('user').filter(hotel=h))
        staff = list(HStaff.objects.select_related('user').filter(hotel=h))
        hotels_roles.append({'hotel': h, 'admins': admins, 'staff': staff})
        roles_chart_labels.append(h.name)
        roles_chart_admins.append(len(admins))
        roles_chart_staff.append(len(staff))
    user_hotels = {}
    if users:
        admin_links = HAdmin.objects.select_related('hotel').filter(user__in=users)
        staff_links = HStaff.objects.select_related('hotel').filter(user__in=users)
        for a in admin_links:
            user_hotels.setdefault(a.user_id, []).append({'hotel_id': a.hotel_id, 'hotel_name': a.hotel.name, 'role': 'admin'})
        for s in staff_links:
            user_hotels.setdefault(s.user_id, []).append({'hotel_id': s.hotel_id, 'hotel_name': s.hotel.name, 'role': 'staff'})
        for u in users:
            setattr(u, 'hotel_links', user_hotels.get(u.id, []))
    context = {
        'users': users,
        'hotels': hotels,
        'hotel_selected': hotel_selected,
        'search': search,
        'hotels_roles': hotels_roles,
        'roles_chart_labels': roles_chart_labels,
        'roles_chart_admins': roles_chart_admins,
        'roles_chart_staff': roles_chart_staff,
        'user_hotels': user_hotels,
    }
    return render(request, 'superadmin/users_list.html', context)

@login_required
def superadmin_export_bookings_csv(request):
    if not is_superadmin(request.user):
        return HttpResponseForbidden()
    from app.bookings.models import Booking
    import csv
    from io import StringIO
    hotel_id = request.GET.get('hotel')
    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')
    qs = Booking.objects.select_related('client', 'room', 'hotel')
    if hotel_id:
        try:
            h = Hotel.objects.get(id=hotel_id)
            qs = qs.filter(hotel=h)
        except Hotel.DoesNotExist:
            qs = qs.none()
    if desde and hasta:
        try:
            from datetime import datetime
            d1 = datetime.strptime(desde, '%Y-%m-%d').date()
            d2 = datetime.strptime(hasta, '%Y-%m-%d').date()
            qs = qs.filter(check_in_date__gte=d1, check_out_date__lte=d2)
        except Exception:
            qs = qs.none()
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['id', 'hotel', 'habitacion', 'cliente', 'check_in', 'check_out', 'estado', 'total_price'])
    for b in qs.order_by('-created_at')[:1000]:
        writer.writerow([b.id, getattr(b.hotel, 'name', ''), getattr(b.room, 'number', ''), getattr(b.client, 'full_name', ''), b.check_in_date, b.check_out_date, b.status, b.total_price])
    resp = HttpResponse(buffer.getvalue(), content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="reservas.csv"'
    return resp
def get_hotel_activo(request):
    hotel_param = request.GET.get('hotel') or request.POST.get('hotel')
    if hotel_param:
        try:
            return Hotel.objects.get(id=int(hotel_param))
        except Exception:
            try:
                return Hotel.objects.get(slug=str(hotel_param))
            except Hotel.DoesNotExist:
                pass
    try:
        return Hotel.objects.order_by('id').first()
    except Exception:
        return None
# Wrappers slug-based para panel
@login_required
def panel_dashboard_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_staff(request.user, hotel) or is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return dashboard_view(request)

@login_required
def panel_rooms_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_staff(request.user, hotel) or is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return rooms_view(request)

@login_required
def panel_bookings_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_staff(request.user, hotel) or is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return bookings_view(request)

@login_required
def panel_clients_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_staff(request.user, hotel) or is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return clients_view(request)

@login_required
def panel_cleaning_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_staff(request.user, hotel) or is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return cleaning_view(request)

@login_required
def panel_maintenance_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_staff(request.user, hotel) or is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return maintenance_view(request)

@login_required
def panel_administration_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return administration_view(request)

@login_required
def panel_reports_hotel_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    q = request.GET.copy()
    q['hotel'] = hotel_slug
    request.GET = q
    return reports_view(request)

@login_required
@require_http_methods(["POST"])
def panel_change_booking_status_hotel_view(request, hotel_slug, booking_id):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        messages.error(request, 'Hotel no encontrado')
        return redirect('panel_dashboard')
    if not (is_hotel_staff(request.user, hotel) or is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    new_status = request.POST.get('status')
    try:
        b = Booking.objects.get(id=booking_id, hotel=hotel)
        if new_status in dict(Booking.STATUS_CHOICES):
            b.status = new_status
            b.save(update_fields=['status'])
            messages.success(request, 'Estado actualizado')
        else:
            messages.error(request, 'Estado inválido')
    except Booking.DoesNotExist:
        messages.error(request, 'Reserva no encontrada')
    return redirect('panel_booking_detail_hotel', hotel_slug=hotel_slug, booking_id=booking_id)
# ===== CRUD de Usuarios por Hotel (solo hotel_admin o superadmin) =====
@login_required
def hotel_users_list_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    admins = HotelAdmin.objects.filter(hotel=hotel).select_related('user')
    staff = HotelStaff.objects.filter(hotel=hotel).select_related('user')
    return render(request, 'users/list.html', {'hotel': hotel, 'admins': admins, 'staff': staff})

@login_required
def hotel_user_create_view(request, hotel_slug):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'staff')
        if not username or not password:
            messages.error(request, 'Usuario y contraseña son obligatorios')
        else:
            if get_user_model().objects.filter(username=username).exists():
                messages.error(request, 'El usuario ya existe')
            else:
                u = get_user_model().objects.create_user(username=username, email=email, password=password)
                if role == 'admin':
                    HotelAdmin.objects.update_or_create(hotel=hotel, defaults={'user': u})
                    u.is_staff = True
                    u.save(update_fields=['is_staff'])
                else:
                    HotelStaff.objects.update_or_create(hotel=hotel, user=u, defaults={'role': role})
                messages.success(request, 'Usuario creado')
                return redirect('hotel_users_list', hotel_slug=hotel_slug)
    return render(request, 'users/form.html', {'hotel': hotel, 'mode': 'create'})

@login_required
def hotel_user_edit_view(request, hotel_slug, user_id):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    try:
        u = get_user_model().objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponse('Usuario no encontrado', status=404)
    current_role = 'staff'
    if HotelAdmin.objects.filter(hotel=hotel, user=u).exists():
        current_role = 'admin'
    elif HotelStaff.objects.filter(hotel=hotel, user=u).exists():
        st = HotelStaff.objects.get(hotel=hotel, user=u)
        current_role = st.role or 'staff'
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', current_role)
        active = request.POST.get('active') == 'on'
        u.email = email
        u.is_active = active
        u.save(update_fields=['email', 'is_active'])
        if role == 'admin':
            HotelAdmin.objects.update_or_create(hotel=hotel, defaults={'user': u})
            HotelStaff.objects.filter(user=u).delete()
            u.is_staff = True
            u.save(update_fields=['is_staff'])
        else:
            HotelAdmin.objects.filter(hotel=hotel, user=u).delete()
            HotelStaff.objects.update_or_create(hotel=hotel, user=u, defaults={'role': role})
        messages.success(request, 'Usuario actualizado')
        return redirect('hotel_users_list', hotel_slug=hotel_slug)
    return render(request, 'users/form.html', {'hotel': hotel, 'mode': 'edit', 'user_obj': u, 'current_role': current_role})

@login_required
def hotel_user_delete_view(request, hotel_slug, user_id):
    try:
        hotel = Hotel.objects.get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return HttpResponse('Hotel no encontrado', status=404)
    if not (is_hotel_admin(request.user, hotel) or is_superadmin(request.user)):
        return HttpResponseForbidden()
    try:
        u = get_user_model().objects.get(id=user_id)
    except User.DoesNotExist:
        return HttpResponse('Usuario no encontrado', status=404)
    if request.method == 'POST':
        HotelAdmin.objects.filter(hotel=hotel, user=u).delete()
        HotelStaff.objects.filter(hotel=hotel, user=u).delete()
        u.is_active = False
        u.save(update_fields=['is_active'])
        messages.success(request, 'Usuario desactivado y removido de roles del hotel')
        return redirect('hotel_users_list', hotel_slug=hotel_slug)
    return render(request, 'users/confirm_delete.html', {'hotel': hotel, 'user_obj': u})
from django.db import connection
def health_view(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        status = "ok"
    except Exception:
        status = "error"
    return JsonResponse({"status": status})
