from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


phone_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{7,14}$",
    message="Enter a valid international phone number.",
)


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", _("Customer")
        RIDER = "rider", _("Rider")
        DISPATCHER = "dispatcher", _("Dispatcher")
        ADMIN = "admin", _("Admin")

    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(
        max_length=16,
        unique=True,
        validators=[phone_validator],
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER, db_index=True)
    is_verified = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["email", "role"]),
        ]

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)


class Address(TimeStampedModel):
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.CASCADE)
    label = models.CharField(max_length=80)
    contact_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=16, validators=[phone_validator])
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=80, db_index=True)
    state = models.CharField(max_length=80, db_index=True)
    country = models.CharField(max_length=80, default="Nigeria")
    postal_code = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "addresses"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "label"],
                name="unique_address_label_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["city", "state"]),
        ]

    def __str__(self) -> str:
        return f"{self.label} - {self.city}"


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(User, related_name="customer_profile", on_delete=models.CASCADE)
    default_address = models.ForeignKey(
        Address,
        related_name="default_for_customers",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    loyalty_points = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["loyalty_points"])]

    def __str__(self) -> str:
        return f"Customer profile for {self.user.get_full_name() or self.user.username}"
