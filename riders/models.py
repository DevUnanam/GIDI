from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import TimeStampedModel


class RiderProfile(TimeStampedModel):
    class Availability(models.TextChoices):
        OFFLINE = "offline", "Offline"
        AVAILABLE = "available", "Available"
        ON_DELIVERY = "on_delivery", "On delivery"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="rider_profile", on_delete=models.CASCADE)
    license_number = models.CharField(max_length=80, unique=True)
    availability_status = models.CharField(
        max_length=20,
        choices=Availability.choices,
        default=Availability.OFFLINE,
        db_index=True,
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    completed_deliveries = models.PositiveIntegerField(default=0)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_approved = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["availability_status", "is_approved"]),
            models.Index(fields=["rating"]),
        ]

    def clean(self):
        if self.user_id and self.user.role != "rider":
            raise ValidationError("Rider profiles can only be assigned to users with the Rider role.")

    def __str__(self) -> str:
        return f"Rider profile for {self.user.get_full_name() or self.user.username}"


class Vehicle(TimeStampedModel):
    class VehicleType(models.TextChoices):
        BICYCLE = "bicycle", "Bicycle"
        MOTORCYCLE = "motorcycle", "Motorcycle"
        CAR = "car", "Car"
        VAN = "van", "Van"
        TRUCK = "truck", "Truck"

    rider = models.ForeignKey(RiderProfile, related_name="vehicles", on_delete=models.CASCADE)
    vehicle_type = models.CharField(max_length=20, choices=VehicleType.choices, db_index=True)
    make = models.CharField(max_length=80)
    model = models.CharField(max_length=80)
    color = models.CharField(max_length=40)
    plate_number = models.CharField(max_length=30, unique=True)
    capacity_kg = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(capacity_kg__gt=0), name="vehicle_capacity_gt_zero"),
        ]
        indexes = [
            models.Index(fields=["rider", "is_active"]),
            models.Index(fields=["vehicle_type", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.plate_number} ({self.vehicle_type})"
