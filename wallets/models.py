from django.conf import settings
from django.db import models

from accounts.models import TimeStampedModel


class Wallet(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="wallet", on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="NGN")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(balance__gte=0), name="wallet_balance_gte_zero"),
        ]
        indexes = [models.Index(fields=["currency", "is_active"])]

    def __str__(self) -> str:
        return f"{self.user.email} wallet"


class Transaction(TimeStampedModel):
    class TransactionType(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REVERSED = "reversed", "Reversed"

    wallet = models.ForeignKey(Wallet, related_name="transactions", on_delete=models.PROTECT)
    shipment = models.ForeignKey(
        "deliveries.Shipment",
        related_name="wallet_transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=80, unique=True, db_index=True)
    description = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name="transaction_amount_gt_zero"),
        ]
        indexes = [
            models.Index(fields=["wallet", "status"]),
            models.Index(fields=["transaction_type", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.reference
