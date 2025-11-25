from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from .models import HotelAdmin, HotelStaff


@receiver(post_save, sender=HotelAdmin)
def ensure_admin_has_no_staff(sender, instance, **kwargs):
    # Cuando un usuario es admin de un hotel, no debe tener ningún rol de staff en ningún hotel
    HotelStaff.objects.filter(user=instance.user).delete()


@receiver(pre_save, sender=HotelStaff)
def prevent_staff_if_admin(sender, instance, **kwargs):
    # Si el usuario es admin de algún hotel, no puede ser staff
    if HotelAdmin.objects.filter(user=instance.user).exists():
        raise ValidationError('El usuario es admin de un hotel y no puede ser staff')