from django.core.management.base import BaseCommand
from django.db import transaction

from app.administration.models import Hotel
from app.rooms.models import Room


class Command(BaseCommand):
    help = "Asegura el hotel 'The Serene' y aplica plantilla 'nuevo'"

    @transaction.atomic
    def handle(self, *args, **options):
        hotel, created = Hotel.objects.get_or_create(
            slug='the-serene',
            defaults={
                'name': 'The Serene',
                'email_contact': 'reservas@theserene.com',
                'phone': '+54 351 555-0000',
                'address': 'Av. del Lago 123, Córdoba',
                'plan_name': getattr(Hotel, 'PLAN_STARTER', 'starter'),
                'subscription_status': getattr(Hotel, 'SUB_ACTIVE', 'active'),
                'is_blocked': False,
                'template_id': 'nuevo',
            },
        )
        if not created:
            hotel.template_id = 'nuevo'
            try:
                hotel.sync_block_from_subscription()
            except Exception:
                pass
            hotel.save()
        self.stdout.write(self.style.SUCCESS(f"Hotel asegurado: {hotel.slug} plantilla={hotel.template_id}"))

        try:
            type_price = {
                'double': 120,
                'suite': 220,
            }
            rooms_def = [
                (201, 2, 'double', 2),
                (202, 2, 'double', 2),
                (401, 4, 'suite', 3),
            ]
            for num, floor, t, cap in rooms_def:
                Room.objects.get_or_create(
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
            Room.objects.filter(hotel=hotel).update(status='available', active=True)
            self.stdout.write(self.style.SUCCESS("Habitaciones creadas/aseguradas para The Serene"))
        except Exception:
            pass