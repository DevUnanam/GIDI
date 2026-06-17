from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, CustomerProfile, DispatcherProfile, NotificationPreference, User, UserSession


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone_number", "role", "is_verified", "is_active", "is_staff")
    list_filter = ("role", "is_verified", "is_active", "is_staff")
    search_fields = ("username", "email", "phone_number", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = UserAdmin.fieldsets + (
        ("GIDI profile", {"fields": ("phone_number", "role", "is_verified", "avatar")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("GIDI profile", {"fields": ("email", "phone_number", "role")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("label", "user", "city", "state", "contact_phone", "is_default", "created_at")
    list_filter = ("city", "state", "is_default")
    search_fields = ("label", "user__email", "contact_name", "contact_phone", "address_line_1")
    autocomplete_fields = ("user",)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "default_address", "loyalty_points", "marketing_opt_in", "created_at")
    search_fields = ("user__email", "user__username")
    autocomplete_fields = ("user", "default_address")


@admin.register(DispatcherProfile)
class DispatcherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_id", "assigned_zone", "is_on_shift", "can_assign_riders")
    list_filter = ("is_on_shift", "can_assign_riders", "assigned_zone")
    search_fields = ("user__email", "user__username", "employee_id")
    autocomplete_fields = ("user",)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "device_name", "ip_address", "last_seen_at", "expires_at", "revoked_at")
    list_filter = ("revoked_at", "created_at", "last_seen_at")
    search_fields = ("user__email", "device_name", "ip_address", "refresh_jti")
    autocomplete_fields = ("user",)
    readonly_fields = ("refresh_jti", "created_at", "updated_at", "last_seen_at")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email_enabled", "sms_enabled", "push_enabled", "shipment_updates", "payment_updates")
    list_filter = ("email_enabled", "sms_enabled", "push_enabled", "shipment_updates", "payment_updates", "marketing_updates")
    search_fields = ("user__email", "user__username")
    autocomplete_fields = ("user",)
