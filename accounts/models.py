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
    avatar = models.ImageField(upload_to="avatars/%Y/%m/", null=True, blank=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["email", "role"]),
            models.Index(fields=["is_verified", "is_active"]),
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
    marketing_opt_in = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["loyalty_points"])]

    def __str__(self) -> str:
        return f"Customer profile for {self.user.get_full_name() or self.user.username}"


class DispatcherProfile(TimeStampedModel):
    user = models.OneToOneField(User, related_name="dispatcher_profile", on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50, unique=True)
    assigned_zone = models.CharField(max_length=120, blank=True, db_index=True)
    can_assign_riders = models.BooleanField(default=True)
    is_on_shift = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["assigned_zone", "is_on_shift"]),
        ]

    def clean(self):
        if self.user_id and self.user.role != User.Role.DISPATCHER:
            from django.core.exceptions import ValidationError

            raise ValidationError("Dispatcher profiles can only be assigned to Dispatcher users.")

    def __str__(self) -> str:
        return f"Dispatcher profile for {self.user.get_full_name() or self.user.username}"


class UserSession(TimeStampedModel):
    user = models.ForeignKey(User, related_name="sessions", on_delete=models.CASCADE)
    refresh_jti = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "revoked_at"]),
            models.Index(fields=["user", "last_seen_at"]),
        ]

    @property
    def is_active(self) -> bool:
        from django.utils import timezone

        return self.revoked_at is None and self.expires_at > timezone.now()

    def __str__(self) -> str:
        return f"{self.user.email} session {self.refresh_jti[:8]}"


class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(User, related_name="notification_preference", on_delete=models.CASCADE)
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    shipment_updates = models.BooleanField(default=True)
    payment_updates = models.BooleanField(default=True)
    marketing_updates = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["email_enabled", "push_enabled"]),
        ]

    def __str__(self) -> str:
        return f"Notification preferences for {self.user.email}"
