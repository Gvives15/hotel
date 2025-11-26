from django.db import models
from django.conf import settings


PLAN_STARTER = "starter"
PLAN_GROW = "grow"

PLAN_CHOICES = [
    (PLAN_STARTER, "Starter 20"),
    (PLAN_GROW, "Grow 40"),
]

SUB_TRIAL = "trial"
SUB_ACTIVE = "active"
SUB_BLOCKED = "blocked"
SUB_CANCELLED = "cancelled"

SUBSCRIPTION_STATUS_CHOICES = [
    (SUB_TRIAL, "Trial"),
    (SUB_ACTIVE, "Active"),
    (SUB_BLOCKED, "Blocked"),
    (SUB_CANCELLED, "Cancelled"),
]


class Hotel(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    email_contact = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_blocked = models.BooleanField(default=False)
    plan_name = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_STARTER)
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default=SUB_TRIAL)
    trial_until = models.DateField(null=True, blank=True)
    template_id = models.CharField(max_length=50, default='client')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}"

    @property
    def can_accept_new_bookings(self) -> bool:
        return (self.subscription_status in {SUB_TRIAL, SUB_ACTIVE}) and (not self.is_blocked)

    def sync_block_from_subscription(self) -> None:
        if self.subscription_status in {SUB_TRIAL, SUB_ACTIVE}:
            self.is_blocked = False
        else:
            self.is_blocked = True

class HotelAdmin(models.Model):
    hotel = models.OneToOneField(Hotel, on_delete=models.CASCADE, related_name='admin')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hotel_admin')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["hotel__name"]
    
    def __str__(self):
        return f"{self.user.username} -> {self.hotel.slug}"

class HotelStaff(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='staff')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hotel_staff_memberships')
    role = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["hotel__name", "user__username"]
        constraints = [
            models.UniqueConstraint(fields=['hotel', 'user'], name='unique_staff_per_hotel_user')
        ]

    def __str__(self):
        return f"{self.user.username} (staff) -> {self.hotel.slug}"
