from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Client
import random

@receiver(post_save, sender=User)
def create_or_update_client_profile(sender, instance, created, **kwargs):
    """
    Signal para crear o actualizar automáticamente un perfil de Cliente 
    cuando se crea o actualiza un usuario
    """
    try:
        if created:
            # Solo crear si no existe ya un cliente para este usuario
            if not hasattr(instance, 'client') or not Client.objects.filter(user=instance).exists():
                # Generar email único si no tiene
                email = instance.email
                if not email or Client.objects.filter(email=email).exists():
                    email = f'{instance.username}_{random.randint(1000, 9999)}@hotel.com'
                
                # Generar DNI único
                dni = f'{random.randint(10000000, 99999999)}'
                while Client.objects.filter(dni=dni).exists():
                    dni = f'{random.randint(10000000, 99999999)}'
                
                Client.objects.create(
                    user=instance,
                    first_name=instance.first_name or instance.username,
                    last_name=instance.last_name or 'Usuario',
                    email=email,
                    dni=dni,
                    phone=f'+54911{random.randint(1000000, 9999999)}'
                )
        else:
            # Actualizar cliente existente si existe
            try:
                client = instance.client
                # Actualizar datos básicos si están vacíos
                if not client.first_name and instance.first_name:
                    client.first_name = instance.first_name
                if not client.last_name and instance.last_name:
                    client.last_name = instance.last_name
                if not client.email and instance.email:
                    # Verificar que el email no esté en uso por otro cliente
                    if not Client.objects.filter(email=instance.email).exclude(id=client.id).exists():
                        client.email = instance.email
                client.save()
            except Client.DoesNotExist:
                # Si no existe el perfil, no hacer nada
                pass
    except Exception as e:
        # Log del error pero no fallar la creación/actualización del usuario
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al crear/actualizar perfil de cliente para usuario {instance.username}: {str(e)}")