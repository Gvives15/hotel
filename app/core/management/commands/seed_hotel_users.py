from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
import random

from app.administration.models import Hotel, HotelAdmin, HotelStaff


class Command(BaseCommand):
    help = "Crea un usuario admin por hotel y entre 3..10 usuarios staff por hotel"

    def add_arguments(self, parser):
        parser.add_argument('--staff_min', type=int, default=3, help='Cantidad mínima de staff por hotel')
        parser.add_argument('--staff_max', type=int, default=10, help='Cantidad máxima de staff por hotel')
        parser.add_argument('--password_admin', type=str, default='admin123', help='Password por defecto para admins')
        parser.add_argument('--password_staff', type=str, default='staff123', help='Password por defecto para staff')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        staff_min = max(1, int(options.get('staff_min') or 3))
        staff_max = max(staff_min, int(options.get('staff_max') or 10))
        pwd_admin = options.get('password_admin') or 'admin123'
        pwd_staff = options.get('password_staff') or 'staff123'

        admins_created = 0
        staff_created = 0

        for h in Hotel.objects.all().order_by('name'):
            uname = f"admin_{h.slug}"
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f'{uname}@example.com',
                    'is_staff': True,
                },
            )
            u.set_password(pwd_admin)
            u.is_staff = True
            u.save()
            HotelAdmin.objects.update_or_create(hotel=h, defaults={'user': u})
            admins_created += 1

            n_staff = random.randint(staff_min, staff_max)
            for i in range(1, n_staff + 1):
                sname = f"staff_{h.slug}_{i}"
                su, _ = User.objects.get_or_create(
                    username=sname,
                    defaults={'email': f'{sname}@example.com'},
                )
                su.set_password(pwd_staff)
                su.save()
                HotelStaff.objects.get_or_create(hotel=h, user=su, defaults={'role': 'staff'})
                staff_created += 1

        self.stdout.write(self.style.SUCCESS(f"Usuarios creados: admins={admins_created}, staff={staff_created}"))