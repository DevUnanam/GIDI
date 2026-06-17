from django.contrib import admin

from .models import DeliveryProof, Shipment, ShipmentItem, ShipmentStatus


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 0
    readonly_fields = ("created_at", "updated_at")


class ShipmentStatusInline(admin.TabularInline):
    model = ShipmentStatus
    extra = 0
    readonly_fields = ("created_at", "updated_at")


class DeliveryProofInline(admin.StackedInline):
    model = DeliveryProof
    extra = 0
    readonly_fields = ("created_at", "updated_at", "otp_verified", "delivered_at")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("tracking_number", "customer", "rider", "dispatcher", "status", "package_type", "service_level", "delivery_fee", "created_at")
    list_filter = ("status", "package_type", "service_level", "created_at")
    search_fields = ("tracking_number", "customer__email", "recipient_name", "recipient_phone")
    autocomplete_fields = ("customer", "rider", "dispatcher", "pickup_address", "dropoff_address")
    readonly_fields = ("created_at", "updated_at", "delivery_otp_hash", "delivery_otp_expires_at")
    inlines = [ShipmentItemInline, ShipmentStatusInline, DeliveryProofInline]


@admin.register(ShipmentStatus)
class ShipmentStatusAdmin(admin.ModelAdmin):
    list_display = ("shipment", "status", "changed_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("shipment__tracking_number", "notes")
    autocomplete_fields = ("shipment", "changed_by")


@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = ("shipment", "name", "quantity", "weight_kg", "declared_value", "created_at")
    search_fields = ("shipment__tracking_number", "name", "description")
    autocomplete_fields = ("shipment",)


@admin.register(DeliveryProof)
class DeliveryProofAdmin(admin.ModelAdmin):
    list_display = ("shipment", "verified_by", "receiver_name", "otp_verified", "delivered_at")
    list_filter = ("otp_verified", "delivered_at")
    search_fields = ("shipment__tracking_number", "receiver_name", "receiver_phone")
    autocomplete_fields = ("shipment", "verified_by")
    readonly_fields = ("created_at", "updated_at", "otp_verified", "delivered_at")
