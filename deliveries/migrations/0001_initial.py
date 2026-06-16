# Generated for GIDI Phase 1.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("riders", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tracking_number", models.CharField(db_index=True, max_length=32, unique=True)),
                ("service_level", models.CharField(choices=[("standard", "Standard"), ("express", "Express"), ("same_day", "Same day")], default="standard", max_length=20)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("pending", "Pending"), ("assigned", "Assigned"), ("picked_up", "Picked up"), ("in_transit", "In transit"), ("delivered", "Delivered"), ("cancelled", "Cancelled"), ("failed", "Failed")], db_index=True, default="draft", max_length=20)),
                ("package_description", models.CharField(max_length=255)),
                ("package_weight_kg", models.DecimalField(decimal_places=2, max_digits=8)),
                ("package_value", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("delivery_fee", models.DecimalField(decimal_places=2, max_digits=12)),
                ("scheduled_pickup_at", models.DateTimeField(blank=True, null=True)),
                ("picked_up_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("recipient_name", models.CharField(max_length=150)),
                ("recipient_phone", models.CharField(max_length=16)),
                ("delivery_notes", models.TextField(blank=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="shipments", to=settings.AUTH_USER_MODEL)),
                ("dropoff_address", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="dropoff_shipments", to="accounts.address")),
                ("pickup_address", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pickup_shipments", to="accounts.address")),
                ("rider", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="shipments", to="riders.riderprofile")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["customer", "status"], name="deliveries__custome_0b4a5a_idx"),
                    models.Index(fields=["rider", "status"], name="deliveries__rider_i_23856c_idx"),
                    models.Index(fields=["status", "created_at"], name="deliveries__status_9a37f4_idx"),
                    models.Index(fields=["service_level", "status"], name="deliveries__service_6fca40_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(check=models.Q(("package_weight_kg__gt", 0)), name="shipment_weight_gt_zero"),
                    models.CheckConstraint(check=models.Q(("delivery_fee__gte", 0)), name="shipment_delivery_fee_gte_zero"),
                    models.CheckConstraint(check=models.Q(("package_value__gte", 0)), name="shipment_package_value_gte_zero"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ShipmentStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("pending", "Pending"), ("assigned", "Assigned"), ("picked_up", "Picked up"), ("in_transit", "In transit"), ("delivered", "Delivered"), ("cancelled", "Cancelled"), ("failed", "Failed")], db_index=True, max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="shipment_status_changes", to=settings.AUTH_USER_MODEL)),
                ("shipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_history", to="deliveries.shipment")),
            ],
            options={
                "verbose_name_plural": "shipment statuses",
                "indexes": [
                    models.Index(fields=["shipment", "created_at"], name="deliveries__shipmen_d605db_idx"),
                    models.Index(fields=["status", "created_at"], name="deliveries__status_7f1c78_idx"),
                ],
            },
        ),
    ]
