from django.contrib import admin
from .models import Hotel, HotelAdmin as HotelAdminModel, HotelStaff


@admin.register(Hotel)
class HotelModelAdmin(admin.ModelAdmin):
    list_display = ("name", "plan_name", "subscription_status", "is_blocked", "slug", "email_contact", "phone")
    list_filter = ("plan_name", "subscription_status", "is_blocked")
    search_fields = ("name", "slug", "email_contact", "phone")
    fields = (
        "name",
        "slug",
        "email_contact",
        "phone",
        "address",
        "plan_name",
        "subscription_status",
        "trial_until",
        "is_blocked",
    )
    readonly_fields = ("created_at", "updated_at", "is_blocked")

    actions = (
        "set_subscription_trial",
        "set_subscription_active",
        "set_subscription_blocked",
        "set_plan_starter",
        "set_plan_grow",
    )

    def save_model(self, request, obj, form, change):
        try:
            obj.sync_block_from_subscription()
        except Exception:
            pass
        super().save_model(request, obj, form, change)

    def set_subscription_trial(self, request, queryset):
        updated = queryset.update(subscription_status="trial")
        for hotel in queryset:
            try:
                hotel.sync_block_from_subscription()
                hotel.save(update_fields=["is_blocked", "subscription_status", "updated_at"])
            except Exception:
                pass
        self.message_user(request, f"{updated} hoteles pasados a Trial")
    set_subscription_trial.short_description = "Establecer suscripción: Trial"

    def set_subscription_active(self, request, queryset):
        updated = queryset.update(subscription_status="active")
        for hotel in queryset:
            try:
                hotel.sync_block_from_subscription()
                hotel.save(update_fields=["is_blocked", "subscription_status", "updated_at"])
            except Exception:
                pass
        self.message_user(request, f"{updated} hoteles activados")
    set_subscription_active.short_description = "Establecer suscripción: Activa"

    def set_subscription_blocked(self, request, queryset):
        updated = queryset.update(subscription_status="blocked")
        for hotel in queryset:
            try:
                hotel.sync_block_from_subscription()
                hotel.save(update_fields=["is_blocked", "subscription_status", "updated_at"])
            except Exception:
                pass
        self.message_user(request, f"{updated} hoteles bloqueados")
    set_subscription_blocked.short_description = "Establecer suscripción: Bloqueada"

    def set_plan_starter(self, request, queryset):
        updated = queryset.update(plan_name="starter")
        self.message_user(request, f"{updated} hoteles configurados al plan Starter")
    set_plan_starter.short_description = "Establecer plan: Starter"

    def set_plan_grow(self, request, queryset):
        updated = queryset.update(plan_name="grow")
        self.message_user(request, f"{updated} hoteles configurados al plan Grow")
    set_plan_grow.short_description = "Establecer plan: Grow"

@admin.register(HotelAdminModel)
class HotelAdminAdmin(admin.ModelAdmin):
    list_display = ("hotel", "user", "created_at", "updated_at")
    list_filter = ("hotel",)
    search_fields = ("hotel__name", "hotel__slug", "user__username", "user__email")

@admin.register(HotelStaff)
class HotelStaffAdmin(admin.ModelAdmin):
    list_display = ("hotel", "user", "role", "created_at", "updated_at")
    list_filter = ("hotel", "role")
    search_fields = ("hotel__name", "hotel__slug", "user__username", "user__email", "role")

# Register your models here.
