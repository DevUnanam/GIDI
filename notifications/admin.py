from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "channel", "is_read", "created_at")
    list_filter = ("notification_type", "channel", "is_read", "created_at")
    search_fields = ("title", "message", "user__email", "shipment__tracking_number")
    autocomplete_fields = ("user", "shipment")
    readonly_fields = ("created_at", "updated_at")
