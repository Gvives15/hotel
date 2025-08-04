from django.core.management.base import BaseCommand
from app.core.services import EmailService
from app.bookings.models import Booking
from app.clients.models import Client

class Command(BaseCommand):
    help = 'Prueba el envío de emails del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['booking', 'welcome'],
            default='booking',
            help='Tipo de email a probar (booking o welcome)'
        )
        parser.add_argument(
            '--id',
            type=int,
            help='ID de la reserva o cliente'
        )

    def handle(self, *args, **options):
        email_type = options['type']
        obj_id = options['id']

        if not obj_id:
            self.stdout.write(
                self.style.ERROR('Debes especificar un ID con --id')
            )
            return

        if email_type == 'booking':
            self.test_booking_email(obj_id)
        elif email_type == 'welcome':
            self.test_welcome_email(obj_id)

    def test_booking_email(self, booking_id):
        """Prueba el envío de email de confirmación de reserva"""
        try:
            booking = Booking.objects.get(id=booking_id)
            self.stdout.write(
                self.style.SUCCESS(f'Probando email de confirmación para reserva #{booking_id}')
            )
            
            result = EmailService.send_booking_confirmation(booking_id)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Email enviado exitosamente a {result["recipient_email"]}')
                )
                self.stdout.write(f'   - Asunto: {result["subject"]}')
                self.stdout.write(f'   - Log ID: {result["email_log_id"]}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error al enviar email: {result["message"]}')
                )
                
        except Booking.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Reserva #{booking_id} no encontrada')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error inesperado: {str(e)}')
            )

    def test_welcome_email(self, client_id):
        """Prueba el envío de email de bienvenida"""
        try:
            client = Client.objects.get(id=client_id)
            self.stdout.write(
                self.style.SUCCESS(f'Probando email de bienvenida para cliente #{client_id}')
            )
            
            result = EmailService.send_welcome_email(client_id)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Email de bienvenida enviado exitosamente a {result["recipient_email"]}')
                )
                self.stdout.write(f'   - Log ID: {result["email_log_id"]}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error al enviar email: {result["message"]}')
                )
                
        except Client.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Cliente #{client_id} no encontrado')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error inesperado: {str(e)}')
            ) 