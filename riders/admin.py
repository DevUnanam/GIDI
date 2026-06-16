from django.contrib import admin

from .models import RiderProfile, Vehicle


@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "availability_status", "is_approved", "rating", "completed_deliveries")
    list_filter = ("availability_status", "is_approved")
    search_fields = ("user__email", "user__username", "license_number")
    autocomplete_fields = ("user",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "rider", "vehicle_type", "make", "model", "capacity_kg", "is_active")
    list_filter = ("vehicle_type", "is_active")
    search_fields = ("plate_number", "make", "model", "rider__user__email")
    autocomplete_fields = ("rider",)
