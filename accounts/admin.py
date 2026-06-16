from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, CustomerProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone_number", "role", "is_verified", "is_active", "is_staff")
    list_filter = ("role", "is_verified", "is_active", "is_staff")
    search_fields = ("username", "email", "phone_number", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = UserAdmin.fieldsets + (
        ("GIDI profile", {"fields": ("phone_number", "role", "is_verified")}),
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
    list_display = ("user", "default_address", "loyalty_points", "created_at")
    search_fields = ("user__email", "user__username")
    autocomplete_fields = ("user", "default_address")
