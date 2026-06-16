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
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("notification_type", models.CharField(choices=[("shipment", "Shipment"), ("payment", "Payment"), ("wallet", "Wallet"), ("system", "System")], db_index=True, max_length=20)),
                ("channel", models.CharField(choices=[("in_app", "In app"), ("email", "Email"), ("sms", "SMS"), ("push", "Push")], db_index=True, default="in_app", max_length=20)),
                ("title", models.CharField(max_length=120)),
                ("message", models.TextField()),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("shipment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications", to="deliveries.shipment")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "is_read"], name="notificatio_user_id_7f357f_idx"),
                    models.Index(fields=["notification_type", "created_at"], name="notificatio_notific_7fcfa7_idx"),
                    models.Index(fields=["channel", "created_at"], name="notificatio_channel_096fb4_idx"),
                ],
            },
        ),
    ]
