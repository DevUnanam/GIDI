# Generated for GIDI Phase 1.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("deliveries", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("wallets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider", models.CharField(choices=[("paystack", "Paystack"), ("flutterwave", "Flutterwave"), ("wallet", "Wallet"), ("cash", "Cash")], db_index=True, max_length=20)),
                ("status", models.CharField(choices=[("initiated", "Initiated"), ("processing", "Processing"), ("success", "Success"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("refunded", "Refunded")], db_index=True, default="initiated", max_length=20)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="NGN", max_length=3)),
                ("reference", models.CharField(db_index=True, max_length=80, unique=True)),
                ("provider_reference", models.CharField(blank=True, db_index=True, max_length=120)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("shipment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="deliveries.shipment")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to=settings.AUTH_USER_MODEL)),
                ("wallet_transaction", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payment", to="wallets.transaction")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "status"], name="payments_pa_user_id_403cf4_idx"),
                    models.Index(fields=["shipment", "status"], name="payments_pa_shipmen_872e63_idx"),
                    models.Index(fields=["provider", "status"], name="payments_pa_provide_b4de1a_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(check=models.Q(("amount__gt", 0)), name="payment_amount_gt_zero"),
                ],
            },
        ),
    ]
