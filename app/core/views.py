from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from datetime import datetime, timedelta

# Importar modelos de las apps
try:
    from app.rooms.models import Room
    from app.bookings.models import Booking
    from app.clients.models import Client
    from app.cleaning.models import CleaningTask
    from app.maintenance.models import MaintenanceRequest
except ImportError:
    # Si los modelos no existen, crear placeholders
    Room = None
    Booking = None
    Client = None
    CleaningTask = None
    MaintenanceRequest = None

def login_view(request):
    """Vista para el login"""
    if request.user.is_authenticated:
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

@login_required
def dashboard_view(request):
    """Vista del dashboard principal"""
    context = {}
    
    # Obtener estadísticas básicas
    if Room:
        context['total_rooms'] = Room.objects.count()
        context['available_rooms'] = Room.objects.filter(status='available').count()
        context['occupied_rooms'] = Room.objects.filter(status='occupied').count()
        context['cleaning_rooms'] = Room.objects.filter(status='cleaning').count()
        context['maintenance_rooms'] = Room.objects.filter(status='maintenance').count()
    else:
        # Datos de ejemplo si no hay modelos
        context.update({
            'total_rooms': 50,
            'available_rooms': 35,
            'occupied_rooms': 12,
            'cleaning_rooms': 2,
            'maintenance_rooms': 1
        })
    
    if Booking:
        # Reservas activas (check-in <= hoy <= check-out)
        today = datetime.now().date()
        context['active_bookings'] = Booking.objects.filter(
            check_in__lte=today,
            check_out__gte=today,
            status='active'
        ).count()
        
        # Reservas recientes
        context['recent_bookings'] = Booking.objects.select_related('client', 'room').order_by('-created_at')[:10]
        
        # Ingresos del mes actual
        start_of_month = datetime.now().replace(day=1).date()
        context['total_revenue'] = Booking.objects.filter(
            check_in__gte=start_of_month,
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
    else:
        context.update({
            'active_bookings': 15,
            'recent_bookings': [],
            'total_revenue': 25000
        })
    
    if Client:
        context['total_clients'] = Client.objects.count()
    else:
        context['total_clients'] = 120
    
    if MaintenanceRequest:
        # Alertas de mantenimiento pendientes
        context['maintenance_alerts'] = MaintenanceRequest.objects.select_related('room').filter(
            status='pending'
        ).order_by('-priority', '-created_at')[:5]
    else:
        context['maintenance_alerts'] = []
    
    if CleaningTask:
        # Programación de limpieza
        context['cleaning_schedule'] = CleaningTask.objects.select_related('room', 'employee').filter(
            scheduled_date__gte=datetime.now().date()
        ).order_by('scheduled_date')[:10]
    else:
        context['cleaning_schedule'] = []
    
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

# Vistas placeholder para las diferentes secciones
@login_required
def rooms_view(request):
    """Vista de habitaciones"""
    if Room:
        rooms = Room.objects.all()
    else:
        rooms = []
    return render(request, 'rooms/list.html', {'rooms': rooms})

@login_required
def bookings_view(request):
    """Vista de reservas"""
    if Booking:
        bookings = Booking.objects.select_related('client', 'room').all()
    else:
        bookings = []
    return render(request, 'bookings/list.html', {'bookings': bookings})

@login_required
def clients_view(request):
    """Vista de clientes"""
    if Client:
        clients = Client.objects.all()
    else:
        clients = []
    return render(request, 'clients/list.html', {'clients': clients})

@login_required
def cleaning_view(request):
    """Vista de limpieza"""
    if CleaningTask:
        tasks = CleaningTask.objects.select_related('room', 'employee').all()
    else:
        tasks = []
    return render(request, 'cleaning/list.html', {'tasks': tasks})

@login_required
def maintenance_view(request):
    """Vista de mantenimiento"""
    if MaintenanceRequest:
        requests = MaintenanceRequest.objects.select_related('room').all()
    else:
        requests = []
    return render(request, 'maintenance/list.html', {'requests': requests})

@login_required
def administration_view(request):
    """Vista de administración"""
    return render(request, 'administration/dashboard.html')

@login_required
def reports_view(request):
    """Vista de reportes"""
    return render(request, 'reports/dashboard.html')

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

def client_rooms_view(request):
    """Vista de habitaciones disponibles para clientes"""
    if Room:
        rooms = Room.objects.filter(active=True)
        
        # Filtros
        room_type = request.GET.get('type')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        guests = request.GET.get('guests')
        
        if room_type:
            rooms = rooms.filter(type=room_type)
        if min_price:
            rooms = rooms.filter(price__gte=min_price)
        if max_price:
            rooms = rooms.filter(price__lte=max_price)
        if guests:
            rooms = rooms.filter(capacity__gte=guests)
    else:
        rooms = []
    
    context = {
        'rooms': rooms,
        'room_types': Room.TYPE_CHOICES if Room else [],
    }
    
    return render(request, 'client/rooms.html', context)

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

def client_booking_view(request, room_id=None):
    """Vista para crear una reserva"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para hacer una reserva.')
        return redirect('client_login')
    
    if Room:
        if room_id:
            try:
                room = Room.objects.get(id=room_id, active=True)
            except Room.DoesNotExist:
                messages.error(request, 'Habitación no encontrada.')
                return redirect('client_rooms')
        else:
            room = None
    else:
        room = None
    
    if request.method == 'POST':
        # Procesar la reserva
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        guests_count = request.POST.get('guests_count')
        special_requests = request.POST.get('special_requests')
        
        if room and check_in and check_out and guests_count:
            try:
                # Crear la reserva
                booking = Booking.objects.create(
                    client=request.user.client if hasattr(request.user, 'client') else None,
                    room=room,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    guests_count=guests_count,
                    special_requests=special_requests,
                    status='pending'
                )
                
                messages.success(request, 'Reserva creada exitosamente. Te contactaremos pronto para confirmarla.')
                return redirect('client_my_bookings')
            except Exception as e:
                messages.error(request, f'Error al crear la reserva: {str(e)}')
        else:
            messages.error(request, 'Por favor completa todos los campos requeridos.')
    
    context = {
        'room': room,
        'available_rooms': Room.objects.filter(active=True) if Room else [],
    }
    
    return render(request, 'client/booking.html', context)

def client_my_bookings_view(request):
    """Vista de las reservas del cliente"""
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver tus reservas.')
        return redirect('client_login')
    
    if Booking:
        # Obtener reservas del cliente actual
        bookings = Booking.objects.filter(
            client__user=request.user
        ).select_related('room').order_by('-created_at')
    else:
        bookings = []
    
    context = {
        'bookings': bookings,
    }
    
    return render(request, 'client/my_bookings.html', context)

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

def client_login_view(request):
    """Vista de login para clientes"""
    if request.user.is_authenticated:
        return redirect('client_index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f'¡Bienvenido, {user.get_full_name() or user.username}!')
            return redirect('client_index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'client/login.html')

def client_register_view(request):
    """Vista de registro para clientes"""
    if request.user.is_authenticated:
        return redirect('client_index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            
            # Crear cliente asociado si el modelo existe
            if Client:
                client = Client.objects.create(
                    user=user,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email=user.email,
                    phone=request.POST.get('phone', ''),
                    address=request.POST.get('address', ''),
                    nationality=request.POST.get('nationality', ''),
                )
            
            # Autenticar al usuario después del registro
            login(request, user)
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('client_index')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = UserCreationForm()
    
    return render(request, 'client/register.html', {'form': form})

def client_logout_view(request):
    """Vista para cerrar sesión de clientes"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('client_index')
