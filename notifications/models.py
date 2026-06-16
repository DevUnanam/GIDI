from django.conf import settings
from django.db import models

from accounts.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Channel(models.TextChoices):
        IN_APP = "in_app", "In app"
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        PUSH = "push", "Push"

    class NotificationType(models.TextChoices):
        SHIPMENT = "shipment", "Shipment"
        PAYMENT = "payment", "Payment"
        WALLET = "wallet", "Wallet"
        SYSTEM = "system", "System"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="notifications", on_delete=models.CASCADE)
    shipment = models.ForeignKey(
        "deliveries.Shipment",
        related_name="notifications",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, db_index=True)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP, db_index=True)
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notification_type", "created_at"]),
            models.Index(fields=["channel", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.title
