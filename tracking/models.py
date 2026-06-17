from django.conf import settings
from django.db import models

from accounts.models import TimeStampedModel


class TrackingEvent(TimeStampedModel):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending"
        ASSIGNED = "assigned", "Assigned"
        ACCEPTED = "accepted", "Accepted"
        PICKUP_STARTED = "pickup_started", "Pickup started"
        PICKED_UP = "picked_up", "Picked up"
        IN_TRANSIT = "in_transit", "In transit"
        NEAR_DESTINATION = "near_destination", "Near destination"
        LOCATION_UPDATE = "location_update", "Location update"
        DELIVERY_ATTEMPTED = "delivery_attempted", "Delivery attempted"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        RETURNED = "returned", "Returned"

    shipment = models.ForeignKey("deliveries.Shipment", related_name="tracking_events", on_delete=models.CASCADE)
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    message = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="tracking_events",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["shipment", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.shipment.tracking_number}: {self.event_type}"
