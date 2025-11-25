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
    help = "Seed aleatorio: crea N hoteles con habitaciones y entre M..K reservas por hotel"

    def add_arguments(self, parser):
        parser.add_argument('--hotels', type=int, default=10, help='Cantidad de hoteles a crear')
        parser.add_argument('--bookings_min', type=int, default=10, help='Reservas mínimas por hotel')
        parser.add_argument('--bookings_max', type=int, default=50, help='Reservas máximas por hotel')

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.now().date()
        hotels_count = max(1, int(options.get('hotels') or 10))
        bmin = max(1, int(options.get('bookings_min') or 10))
        bmax = max(bmin, int(options.get('bookings_max') or 50))

        plan_choices = ['starter', 'grow']
        sub_choices = ['trial', 'active']

        def create_random_hotel(idx):
            slug = f"seed-hotel-{idx}"
            name = f"Hotel Seed {idx}"
            hotel, _ = Hotel.objects.get_or_create(
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
            return Booking.objects.filter(
                room=room,
                status__in=['pending', 'confirmed'],
                check_in_date__lt=co,
                check_out_date__gt=ci,
            ).exists()

        created_hotels = 0
        created_bookings = 0

        for i in range(1, hotels_count + 1):
            hotel = create_random_hotel(i)
            rooms = create_rooms_for_hotel(hotel)
            created_hotels += 1
            target = random.randint(bmin, bmax)
            for j in range(target):
                room = random.choice(rooms)
                length = random.randint(1, 5)
                ci = today - timedelta(days=random.randint(0, 60))
                if random.random() < 0.3:
                    ci = today + timedelta(days=random.randint(0, 30))
                co = ci + timedelta(days=length)
                status = random.choices(['confirmed', 'pending', 'cancelled'], weights=[0.6, 0.25, 0.15])[0]
                if status in ['pending', 'confirmed'] and has_conflict(room, ci, co):
                    continue
                client = ensure_client_for_hotel(hotel, j + 1)
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
            Room.objects.filter(hotel=hotel).update(status='available', active=True)

        self.stdout.write(self.style.SUCCESS(f"Seed aleatorio completado: hoteles={created_hotels}, reservas={created_bookings}"))