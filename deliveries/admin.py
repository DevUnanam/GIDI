from django.contrib import admin

from .models import Shipment, ShipmentStatus


class ShipmentStatusInline(admin.TabularInline):
    model = ShipmentStatus
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("tracking_number", "customer", "rider", "status", "service_level", "delivery_fee", "created_at")
    list_filter = ("status", "service_level", "created_at")
    search_fields = ("tracking_number", "customer__email", "recipient_name", "recipient_phone")
    autocomplete_fields = ("customer", "rider", "pickup_address", "dropoff_address")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ShipmentStatusInline]


@admin.register(ShipmentStatus)
class ShipmentStatusAdmin(admin.ModelAdmin):
    list_display = ("shipment", "status", "changed_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("shipment__tracking_number", "notes")
    autocomplete_fields = ("shipment", "changed_by")
