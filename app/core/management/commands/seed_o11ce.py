from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import random
import hashlib

from app.administration.models import Hotel
from app.rooms.models import Room
from app.bookings.models import Booking
from app.clients.models import Client


class Command(BaseCommand):
    help = "Seed de datos coherentes para Hotel O11CE y Hotel Demo (multi-hotel) relativo a hoy"

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Limpiar bookings del rango antes de crear')
        parser.add_argument('--random_hotels', type=int, default=0, help='Cantidad de hoteles aleatorios a generar')
        parser.add_argument('--bookings_min', type=int, default=10, help='Reservas mínimas por hotel aleatorio')
        parser.add_argument('--bookings_max', type=int, default=50, help='Reservas máximas por hotel aleatorio')
        parser.add_argument('--skip_base', action='store_true', help='Saltar seed base O11CE + Demo')

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.now().date()
        start = today - timedelta(days=19)
        end = today + timedelta(days=5)

        self.stdout.write(self.style.NOTICE(f"Sembrando datos relativos a hoy={today} (rango {start} → {end})"))

        skip_base = bool(options.get('skip_base'))

        # Crear/obtener hoteles base
        if not skip_base:
            o11ce, _ = Hotel.objects.get_or_create(
            slug='o11ce',
            defaults={
                'name': 'Hotel O11CE',
                'email_contact': 'reservas@hotelo11ce.com',
                'phone': '+54 351 445-0011',
                'address': 'Av. General Paz 1123, Córdoba Capital',
                'plan_name': getattr(Hotel, 'PLAN_STARTER', 'starter'),
                'subscription_status': getattr(Hotel, 'SUB_ACTIVE', 'active'),
                'is_blocked': False,
            },
            )
            try:
                o11ce.sync_block_from_subscription(); o11ce.save()
            except Exception:
                pass
            demo, _ = Hotel.objects.get_or_create(
            slug='demo-mini',
            defaults={
                'name': 'Hotel Demo',
                'email_contact': 'reservas@demo.com',
                'phone': '+54 351 000-0000',
                'address': 'Calle Ficticia 123, Córdoba',
                'plan_name': getattr(Hotel, 'PLAN_GROW', 'grow'),
                'subscription_status': getattr(Hotel, 'SUB_TRIAL', 'trial'),
                'is_blocked': False,
            },
            )
            try:
                demo.sync_block_from_subscription(); demo.save()
            except Exception:
                pass

        if not skip_base:
            # Crear habitaciones O11CE si no existen (40 total)
        type_price = {
            'individual': 80,
            'double': 120,
            'triple': 160,
            'suite': 220,
        }

        def ensure_room(hotel, number, floor, type_key, capacity):
            room, created = Room.objects.get_or_create(
                hotel=hotel, number=str(number),
                defaults={
                    'type': type_key,
                    'capacity': capacity,
                    'status': 'available',
                    'price': type_price[type_key],
                    'floor': floor,
                    'active': True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Room creada {hotel.slug} #{number}"))
            return room

        # 101–110 single
        for n in range(101, 111):
            ensure_room(o11ce, n, 1, 'individual', 1)
        # 201–215 double
        for n in range(201, 216):
            ensure_room(o11ce, n, 2, 'double', 2)
        # 301–310 triple
        for n in range(301, 311):
            ensure_room(o11ce, n, 3, 'triple', 3)
        # 401–405 suite
        for n in range(401, 406):
            ensure_room(o11ce, n, 4, 'suite', 3)

            # Crear habitaciones demo (5)
            for n in range(501, 506):
                ensure_room(demo, n, 5, 'double', 2)

        # Idempotencia: limpiar bookings del rango SOLO de O11CE si --reset
        if not skip_base and options.get('reset'):
            deleted = Booking.objects.filter(hotel=o11ce, check_in_date__gte=start, check_in_date__lte=end).delete()[0]
            # Reset status de rooms O11CE
            Room.objects.filter(hotel=o11ce).update(status='available', active=True)
            self.stdout.write(self.style.WARNING(f"Bookings O11CE en rango eliminados: {deleted}"))

        # Helpers clientes
        def ensure_client(email, first_name, last_name, hotel):
            seed = f"{email}|{hotel.slug}"
            base = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
            dni_num = 10000000 + (base % 90000000)
            client, _ = Client.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': '',
                    'dni': str(dni_num),
                    'hotel': hotel,
                },
            )
            if client.hotel_id != hotel.id:
                client.hotel = hotel
                client.save(update_fields=['hotel'])
            return client

        if not skip_base:
            # Crear bloque de ocupación hoy: 25 rooms confirmadas solapando hoy
        occupy_rooms_numbers = list(range(101, 111)) + list(range(201, 211)) + list(range(301, 306))  # 10 + 10 + 5 = 25
        for idx, num in enumerate(occupy_rooms_numbers, start=1):
            room = Room.objects.get(hotel=o11ce, number=str(num))
            client = ensure_client(f"ocupacion{idx}@o11ce.test", f"Cliente{idx}", "Ocupacion", o11ce)
            booking = Booking(
                hotel=o11ce,
                client=client,
                room=room,
                check_in_date=today - timedelta(days=2),
                check_out_date=today + timedelta(days=2),
                status='confirmed',
                payment_status='paid',
                paid_amount=room.price * 2,
                guests_count=min(room.capacity, 2),
                total_price=room.price * 4,
            )
            booking.save(skip_validation=True)
            # mantener habitaciones disponibles para permitir otras reservas en fechas distintas

        if not skip_base:
            # Tres check-in hoy: pending, confirmed, cancelled
        for mark, st in enumerate(['confirmed', 'pending', 'cancelled'], start=1):
            num = 306 + mark  # 307, 308, 309
            room = Room.objects.get(hotel=o11ce, number=str(num))
            client = ensure_client(f"checkin{mark}@o11ce.test", f"Checkin{mark}", "Hoy", o11ce)
            booking = Booking(
                hotel=o11ce,
                client=client,
                room=room,
                check_in_date=today,
                check_out_date=today + timedelta(days=2),
                status=st,
                payment_status='pending',
                paid_amount=0,
                guests_count=min(room.capacity, 2),
                total_price=room.price * 2,
            )
            booking.save(skip_validation=True)
            # no cambiar estado para no bloquear creación de otras reservas

        if not skip_base:
            # Reservas de primeros días (distribución)
        early_cases = [
            (101, start + timedelta(days=1), start + timedelta(days=4), 'confirmed', 'Juan', 'Perez'),
            (102, start + timedelta(days=2), start + timedelta(days=3), 'cancelled', 'Maria', 'Lopez'),
            (201, start + timedelta(days=4), start + timedelta(days=7), 'confirmed', 'Carlos', 'Ruiz'),
            (202, start + timedelta(days=6), start + timedelta(days=9), 'confirmed', 'TechCor', 'SA'),
            (203, start + timedelta(days=8), start + timedelta(days=10), 'pending', 'Ana', 'Gomez'),
        ]
        for num, ci, co, st, fn, ln in early_cases:
            room = Room.objects.get(hotel=o11ce, number=str(num))
            if room.status != 'available' or not room.active:
                room.status = 'available'
                room.active = True
                room.save(update_fields=['status', 'active'])
            client = ensure_client(f"early{num}@o11ce.test", fn, ln, o11ce)
            booking = Booking(
                hotel=o11ce, client=client, room=room,
                check_in_date=ci, check_out_date=co, status=st,
                payment_status='pending', paid_amount=0,
                guests_count=min(room.capacity, 2), total_price=room.price * max((co - ci).days, 1)
            )
            booking.save(skip_validation=True)

        if not skip_base:
            # Reservas mitad de mes
        mid_cases = [
            (204, start + timedelta(days=11), start + timedelta(days=14), 'confirmed', 'Pedro', 'Sanchez'),
            (205, start + timedelta(days=12), start + timedelta(days=15), 'cancelled', 'Lucia', 'Martinez'),
            (206, start + timedelta(days=13), start + timedelta(days=16), 'confirmed', 'Corp', 'Booking'),
        ]
        for num, ci, co, st, fn, ln in mid_cases:
            room = Room.objects.get(hotel=o11ce, number=str(num))
            if room.status != 'available' or not room.active:
                room.status = 'available'
                room.active = True
                room.save(update_fields=['status', 'active'])
            client = ensure_client(f"mid{num}@o11ce.test", fn, ln, o11ce)
            booking = Booking(
                hotel=o11ce, client=client, room=room,
                check_in_date=ci, check_out_date=co, status=st,
                payment_status='pending', paid_amount=0,
                guests_count=min(room.capacity, 2), total_price=room.price * max((co - ci).days, 1)
            )
            booking.save(skip_validation=True)

        if not skip_base:
            # Reserva futura cancelada
        room401 = Room.objects.get(hotel=o11ce, number='401')
        client401 = ensure_client("future401@o11ce.test", "Futuro", "Cancel", o11ce)
        booking = Booking(
            hotel=o11ce, client=client401, room=room401,
            check_in_date=today + timedelta(days=5), check_out_date=today + timedelta(days=8),
            status='cancelled', payment_status='pending', paid_amount=0,
            guests_count=min(room401.capacity, 2), total_price=room401.price * 3
        )
        booking.save(skip_validation=True)

        if not skip_base:
            # Hotel Demo: 5 rooms, 3 bookings
            demo_rooms = list(Room.objects.filter(hotel=demo).order_by('number'))
            if demo_rooms:
            dclient1 = ensure_client("demo1@demo.test", "Demo", "Uno", demo)
            dclient2 = ensure_client("demo2@demo.test", "Demo", "Dos", demo)
            dclient3 = ensure_client("demo3@demo.test", "Demo", "Tres", demo)
            b1 = Booking(hotel=demo, client=dclient1, room=demo_rooms[0],
                         check_in_date=start + timedelta(days=10), check_out_date=start + timedelta(days=12),
                         status='confirmed', payment_status='paid', paid_amount=demo_rooms[0].price*2,
                         guests_count=2, total_price=demo_rooms[0].price*2)
            b1.save(skip_validation=True)
            b2 = Booking(hotel=demo, client=dclient2, room=demo_rooms[1],
                         check_in_date=start + timedelta(days=12), check_out_date=start + timedelta(days=13),
                         status='cancelled', payment_status='pending', paid_amount=0,
                         guests_count=2, total_price=demo_rooms[1].price)
            b2.save(skip_validation=True)
            b3 = Booking(hotel=demo, client=dclient3, room=demo_rooms[2],
                         check_in_date=today, check_out_date=today + timedelta(days=1),
                         status='pending', payment_status='pending', paid_amount=0,
                         guests_count=2, total_price=demo_rooms[2].price)
            b3.save(skip_validation=True)

        if not skip_base:
            self.stdout.write(self.style.SUCCESS("Seed O11CE + Demo completado"))

        # Generar hoteles aleatorios si se solicitó
        rnd_hotels = int(options.get('random_hotels') or 0)
        bmin = max(1, int(options.get('bookings_min') or 10))
        bmax = max(bmin, int(options.get('bookings_max') or 50))
        if rnd_hotels > 0:
            self.stdout.write(self.style.NOTICE(f"Generando {rnd_hotels} hoteles aleatorios con reservas [{bmin}..{bmax}]"))

            plan_choices = ['starter', 'grow']
            sub_choices = ['trial', 'active']

            def create_random_hotel(idx):
                slug = f"seed-hotel-{idx}"
                name = f"Hotel Seed {idx}"
                hotel, created = Hotel.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'email_contact': f"reservas+{slug}@example.com",
                        'phone': f"+54 351 4{idx:03d}-{random.randint(1000,9999)}",
                        'address': f"Calle {idx} #{random.randint(100,999)}, Ciudad",
                        'plan_name': random.choice(plan_choices),
                        'subscription_status': random.choice(sub_choices),
                        'is_blocked': False,
                    },
                )
                try:
                    hotel.sync_block_from_subscription(); hotel.save()
                except Exception:
                    pass
                return hotel

            def create_rooms_for_hotel(hotel):
                rooms = []
                type_price = {
                    'individual': 70,
                    'double': 110,
                    'triple': 150,
                    'suite': 220,
                }
                # 20 habitaciones por hotel: 6 individual, 8 double, 4 triple, 2 suite
                numbers = []
                base = random.randint(100, 999)
                for i in range(6): numbers.append((base + i, 'individual', 1, 1))
                for i in range(8): numbers.append((base + 100 + i, 'double', 2, 2))
                for i in range(4): numbers.append((base + 200 + i, 'triple', 3, 3))
                for i in range(2): numbers.append((base + 300 + i, 'suite', 3, 4))
                for num, t, cap, floor in numbers:
                    room, _ = Room.objects.get_or_create(
                        hotel=hotel, number=str(num),
                        defaults={
                            'type': t,
                            'capacity': cap,
                            'status': 'available',
                            'price': type_price[t],
                            'floor': floor,
                            'active': True,
                        },
                    )
                    rooms.append(room)
                return rooms

            def ensure_client_for_hotel(hotel, idx):
                email = f"seed.client{idx}.{hotel.slug}@example.com"
                seed = f"{email}|{hotel.slug}"
                base = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
                dni_num = 10000000 + (base % 90000000)
                client, _ = Client.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': f"Cliente{idx}",
                        'last_name': f"Seed{idx}",
                        'phone': f"+54911{random.randint(1000000,9999999)}",
                        'dni': str(dni_num),
                        'hotel': hotel,
                    },
                )
                if client.hotel_id != hotel.id:
                    client.hotel = hotel
                    client.save(update_fields=['hotel'])
                return client

            def has_conflict(room, ci, co):
                # Conflicto si existe reserva pending/confirmed que solape
                return Booking.objects.filter(
                    room=room,
                    status__in=['pending', 'confirmed'],
                    check_in_date__lt=co,
                    check_out_date__gt=ci,
                ).exists()

            created_hotels = 0
            created_bookings = 0
            for i in range(1, rnd_hotels + 1):
                hotel = create_random_hotel(i)
                rooms = create_rooms_for_hotel(hotel)
                created_hotels += 1
                target = random.randint(bmin, bmax)
                # Ventana de fechas: últimos 60 días a próximos 30
                for j in range(target):
                    room = random.choice(rooms)
                    length = random.randint(1, 5)
                    ci = today - timedelta(days=random.randint(0, 60))
                    # aleatoriamente también fechas futuras
                    if random.random() < 0.3:
                        ci = today + timedelta(days=random.randint(0, 30))
                    co = ci + timedelta(days=length)
                    # Determinar estado (más probabilidad de confirmed)
                    status = random.choices(['confirmed', 'pending', 'cancelled'], weights=[0.6, 0.25, 0.15])[0]
                    # Evitar conflicto para pending/confirmed
                    if status in ['pending', 'confirmed'] and has_conflict(room, ci, co):
                        continue
                    client = ensure_client_for_hotel(hotel, j + 1)
                    # Crear booking sin validación para permitir múltiples por habitación en distintas fechas
                    booking = Booking(
                        hotel=hotel,
                        client=client,
                        room=room,
                        check_in_date=ci,
                        check_out_date=co,
                        status=status,
                        payment_status='pending',
                        paid_amount=0,
                        guests_count=min(room.capacity, 2),
                        total_price=room.price * max((co - ci).days, 1),
                    )
                    booking.save(skip_validation=True)
                    created_bookings += 1
                # Restaurar todas las habitaciones a 'available' post-seed
                Room.objects.filter(hotel=hotel).update(status='available', active=True)

            self.stdout.write(self.style.SUCCESS(f"Seed aleatorio completado: hoteles={created_hotels}, reservas={created_bookings}"))