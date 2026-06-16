from django.conf import settings
from django.db import models

from accounts.models import TimeStampedModel


class Payment(TimeStampedModel):
    class Provider(models.TextChoices):
        PAYSTACK = "paystack", "Paystack"
        FLUTTERWAVE = "flutterwave", "Flutterwave"
        WALLET = "wallet", "Wallet"
        CASH = "cash", "Cash"

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PROCESSING = "processing", "Processing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="payments", on_delete=models.PROTECT)
    shipment = models.ForeignKey("deliveries.Shipment", related_name="payments", on_delete=models.PROTECT)
    wallet_transaction = models.OneToOneField(
        "wallets.Transaction",
        related_name="payment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    provider = models.CharField(max_length=20, choices=Provider.choices, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    reference = models.CharField(max_length=80, unique=True, db_index=True)
    provider_reference = models.CharField(max_length=120, blank=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name="payment_amount_gt_zero"),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["shipment", "status"]),
            models.Index(fields=["provider", "status"]),
        ]

    def __str__(self) -> str:
        return self.reference
