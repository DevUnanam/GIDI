from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import Address, TimeStampedModel


class Shipment(TimeStampedModel):
    class ServiceLevel(models.TextChoices):
        STANDARD = "standard", "Standard"
        EXPRESS = "express", "Express"
        SAME_DAY = "same_day", "Same day"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        ASSIGNED = "assigned", "Assigned"
        PICKED_UP = "picked_up", "Picked up"
        IN_TRANSIT = "in_transit", "In transit"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Failed"

    tracking_number = models.CharField(max_length=32, unique=True, db_index=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="shipments", on_delete=models.PROTECT)
    rider = models.ForeignKey(
        "riders.RiderProfile",
        related_name="shipments",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    pickup_address = models.ForeignKey(Address, related_name="pickup_shipments", on_delete=models.PROTECT)
    dropoff_address = models.ForeignKey(Address, related_name="dropoff_shipments", on_delete=models.PROTECT)
    service_level = models.CharField(max_length=20, choices=ServiceLevel.choices, default=ServiceLevel.STANDARD)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    package_description = models.CharField(max_length=255)
    package_weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    package_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2)
    scheduled_pickup_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    recipient_name = models.CharField(max_length=150)
    recipient_phone = models.CharField(max_length=16)
    delivery_notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(package_weight_kg__gt=0), name="shipment_weight_gt_zero"),
            models.CheckConstraint(check=models.Q(delivery_fee__gte=0), name="shipment_delivery_fee_gte_zero"),
            models.CheckConstraint(check=models.Q(package_value__gte=0), name="shipment_package_value_gte_zero"),
        ]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["rider", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["service_level", "status"]),
        ]

    def clean(self):
        if self.customer_id and self.customer.role != "customer":
            raise ValidationError("Shipments can only be created for users with the Customer role.")

    def __str__(self) -> str:
        return self.tracking_number


class ShipmentStatus(TimeStampedModel):
    shipment = models.ForeignKey(Shipment, related_name="status_history", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Shipment.Status.choices, db_index=True)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="shipment_status_changes",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name_plural = "shipment statuses"
        indexes = [
            models.Index(fields=["shipment", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.shipment.tracking_number}: {self.status}"
