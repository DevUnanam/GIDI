# Generated for GIDI Phase 1.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RiderProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("license_number", models.CharField(max_length=80, unique=True)),
                ("availability_status", models.CharField(choices=[("offline", "Offline"), ("available", "Available"), ("on_delivery", "On delivery"), ("suspended", "Suspended")], db_index=True, default="offline", max_length=20)),
                ("rating", models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ("completed_deliveries", models.PositiveIntegerField(default=0)),
                ("current_latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("current_longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("is_approved", models.BooleanField(db_index=True, default=False)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="rider_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["availability_status", "is_approved"], name="riders_ride_availab_cc965d_idx"),
                    models.Index(fields=["rating"], name="riders_ride_rating_418a2d_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="Vehicle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("vehicle_type", models.CharField(choices=[("bicycle", "Bicycle"), ("motorcycle", "Motorcycle"), ("car", "Car"), ("van", "Van"), ("truck", "Truck")], db_index=True, max_length=20)),
                ("make", models.CharField(max_length=80)),
                ("model", models.CharField(max_length=80)),
                ("color", models.CharField(max_length=40)),
                ("plate_number", models.CharField(max_length=30, unique=True)),
                ("capacity_kg", models.DecimalField(decimal_places=2, max_digits=8)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("rider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vehicles", to="riders.riderprofile")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["rider", "is_active"], name="riders_vehi_rider_i_4574c7_idx"),
                    models.Index(fields=["vehicle_type", "is_active"], name="riders_vehi_vehicle_8eb925_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(check=models.Q(("capacity_kg__gt", 0)), name="vehicle_capacity_gt_zero"),
                ],
            },
        ),
    ]
