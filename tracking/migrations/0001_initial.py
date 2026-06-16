# Generated for GIDI Phase 1.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("deliveries", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackingEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(choices=[("created", "Created"), ("assigned", "Assigned"), ("pickup_started", "Pickup started"), ("picked_up", "Picked up"), ("location_update", "Location update"), ("delivery_attempted", "Delivery attempted"), ("delivered", "Delivered"), ("cancelled", "Cancelled")], db_index=True, max_length=30)),
                ("message", models.CharField(max_length=255)),
                ("latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("recorded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tracking_events", to=settings.AUTH_USER_MODEL)),
                ("shipment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tracking_events", to="deliveries.shipment")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["shipment", "created_at"], name="tracking_tr_shipme_7e3e6d_idx"),
                    models.Index(fields=["event_type", "created_at"], name="tracking_tr_event_t_208990_idx"),
                ],
            },
        ),
    ]
