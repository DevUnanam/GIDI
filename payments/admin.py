from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "shipment", "provider", "status", "amount", "currency", "paid_at")
    list_filter = ("provider", "status", "currency", "created_at")
    search_fields = ("reference", "provider_reference", "user__email", "shipment__tracking_number")
    autocomplete_fields = ("user", "shipment", "wallet_transaction")
    readonly_fields = ("created_at", "updated_at")
