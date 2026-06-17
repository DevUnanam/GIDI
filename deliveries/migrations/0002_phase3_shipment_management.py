# Generated for GIDI Phase 3.
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("deliveries", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="shipment",
            name="dispatcher",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="dispatched_shipments", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="shipment",
            name="package_type",
            field=models.CharField(choices=[("document", "Document"), ("parcel", "Parcel"), ("food", "Food"), ("fragile", "Fragile"), ("electronics", "Electronics"), ("other", "Other")], db_index=True, default="parcel", max_length=30),
        ),
        migrations.AddField(
            model_name="shipment",
            name="delivery_otp_hash",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="shipment",
            name="delivery_otp_expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="shipment",
            name="status",
            field=models.CharField(choices=[("pending", "Pending"), ("assigned", "Assigned"), ("accepted", "Accepted"), ("picked_up", "Picked up"), ("in_transit", "In transit"), ("near_destination", "Near destination"), ("delivered", "Delivered"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("returned", "Returned")], db_index=True, default="pending", max_length=24),
        ),
        migrations.AlterField(
            model_name="shipmentstatus",
            name="status",
            field=models.CharField(choices=[("pending", "Pending"), ("assigned", "Assigned"), ("accepted", "Accepted"), ("picked_up", "Picked up"), ("in_transit", "In transit"), ("near_destination", "Near destination"), ("delivered", "Delivered"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("returned", "Returned")], db_index=True, max_length=20),
        ),
        migrations.AddIndex(
            model_name="shipment",
            index=models.Index(fields=["dispatcher", "status"], name="deliveries__dispatc_9fcb8f_idx"),
        ),
        migrations.AddIndex(
            model_name="shipment",
            index=models.Index(fields=["package_type", "status"], name="deliveries__package_565c48_idx"),
        ),
        migrations.CreateModel(
            name="ShipmentItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("weight_kg", models.DecimalField(decimal_places=2, max_digits=8)),
                ("declared_value", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("shipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="deliveries.shipment")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["shipment", "created_at"], name="deliveries__shipmen_90df41_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(check=models.Q(("quantity__gt", 0)), name="shipment_item_quantity_gt_zero"),
                    models.CheckConstraint(check=models.Q(("weight_kg__gt", 0)), name="shipment_item_weight_gt_zero"),
                    models.CheckConstraint(check=models.Q(("declared_value__gte", 0)), name="shipment_item_value_gte_zero"),
                ],
            },
        ),
        migrations.CreateModel(
            name="DeliveryProof",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("receiver_name", models.CharField(max_length=150)),
                ("receiver_phone", models.CharField(max_length=16)),
                ("otp_verified", models.BooleanField(db_index=True, default=False)),
                ("delivery_photo", models.ImageField(blank=True, null=True, upload_to="delivery-proofs/photos/%Y/%m/")),
                ("signature", models.TextField(blank=True)),
                ("signed_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("notes", models.TextField(blank=True)),
                ("shipment", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="delivery_proof", to="deliveries.shipment")),
                ("verified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="delivery_proofs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["otp_verified", "delivered_at"], name="deliveries__otp_ver_9ad4fc_idx"),
                ],
            },
        ),
    ]
