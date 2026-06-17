from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from accounts.models import Address, TimeStampedModel


otp_validator = RegexValidator(regex=r"^\d{6}$", message="OTP must be a 6 digit code.")


class Shipment(TimeStampedModel):
    class ServiceLevel(models.TextChoices):
        STANDARD = "standard", "Standard"
        EXPRESS = "express", "Express"
        SAME_DAY = "same_day", "Same day"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ASSIGNED = "assigned", "Assigned"
        ACCEPTED = "accepted", "Accepted"
        PICKED_UP = "picked_up", "Picked up"
        IN_TRANSIT = "in_transit", "In transit"
        NEAR_DESTINATION = "near_destination", "Near destination"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        RETURNED = "returned", "Returned"

    class PackageType(models.TextChoices):
        DOCUMENT = "document", "Document"
        PARCEL = "parcel", "Parcel"
        FOOD = "food", "Food"
        FRAGILE = "fragile", "Fragile"
        ELECTRONICS = "electronics", "Electronics"
        OTHER = "other", "Other"

    tracking_number = models.CharField(max_length=32, unique=True, db_index=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="shipments", on_delete=models.PROTECT)
    rider = models.ForeignKey(
        "riders.RiderProfile",
        related_name="shipments",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    dispatcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="dispatched_shipments",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    pickup_address = models.ForeignKey(Address, related_name="pickup_shipments", on_delete=models.PROTECT)
    dropoff_address = models.ForeignKey(Address, related_name="dropoff_shipments", on_delete=models.PROTECT)
    service_level = models.CharField(max_length=20, choices=ServiceLevel.choices, default=ServiceLevel.STANDARD)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True)
    package_type = models.CharField(max_length=30, choices=PackageType.choices, default=PackageType.PARCEL, db_index=True)
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
    delivery_otp_hash = models.CharField(max_length=128, blank=True)
    delivery_otp_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(package_weight_kg__gt=0), name="shipment_weight_gt_zero"),
            models.CheckConstraint(check=models.Q(delivery_fee__gte=0), name="shipment_delivery_fee_gte_zero"),
            models.CheckConstraint(check=models.Q(package_value__gte=0), name="shipment_package_value_gte_zero"),
        ]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["rider", "status"]),
            models.Index(fields=["dispatcher", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["service_level", "status"]),
            models.Index(fields=["package_type", "status"]),
        ]

    def clean(self):
        if self.customer_id and self.customer.role != "customer":
            raise ValidationError("Shipments can only be created for users with the Customer role.")
        if self.dispatcher_id and self.dispatcher.role not in {"dispatcher", "admin"}:
            raise ValidationError("Dispatcher must be a Dispatcher or Admin user.")

    def __str__(self) -> str:
        return self.tracking_number

    @property
    def receiver_name(self):
        return self.recipient_name

    @property
    def receiver_phone(self):
        return self.recipient_phone

    @property
    def package_weight(self):
        return self.package_weight_kg

    @property
    def estimated_fee(self):
        return self.delivery_fee


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


class ShipmentItem(TimeStampedModel):
    shipment = models.ForeignKey(Shipment, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    declared_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(quantity__gt=0), name="shipment_item_quantity_gt_zero"),
            models.CheckConstraint(check=models.Q(weight_kg__gt=0), name="shipment_item_weight_gt_zero"),
            models.CheckConstraint(check=models.Q(declared_value__gte=0), name="shipment_item_value_gte_zero"),
        ]
        indexes = [
            models.Index(fields=["shipment", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} x {self.quantity}"


class DeliveryProof(TimeStampedModel):
    shipment = models.OneToOneField(Shipment, related_name="delivery_proof", on_delete=models.CASCADE)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="delivery_proofs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    receiver_name = models.CharField(max_length=150)
    receiver_phone = models.CharField(max_length=16)
    otp_verified = models.BooleanField(default=False, db_index=True)
    delivery_photo = models.ImageField(upload_to="delivery-proofs/photos/%Y/%m/", null=True, blank=True)
    signature = models.TextField(blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(default=timezone.now, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["otp_verified", "delivered_at"]),
        ]

    def clean(self):
        if self.shipment_id and self.shipment.status != Shipment.Status.DELIVERED:
            raise ValidationError("Delivery proof can only be attached to delivered shipments.")

    def __str__(self) -> str:
        return f"Proof for {self.shipment.tracking_number}"
