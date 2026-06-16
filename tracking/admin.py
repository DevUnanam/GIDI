from django.contrib import admin

from .models import TrackingEvent


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    list_display = ("shipment", "event_type", "recorded_by", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("shipment__tracking_number", "message", "recorded_by__email")
    autocomplete_fields = ("shipment", "recorded_by")
    readonly_fields = ("created_at", "updated_at")
