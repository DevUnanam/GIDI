# Generated for GIDI Phase 2.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to="avatars/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="customerprofile",
            name="marketing_opt_in",
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["is_verified", "is_active"], name="accounts_us_is_veri_8568ba_idx"),
        ),
        migrations.CreateModel(
            name="DispatcherProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("employee_id", models.CharField(max_length=50, unique=True)),
                ("assigned_zone", models.CharField(blank=True, db_index=True, max_length=120)),
                ("can_assign_riders", models.BooleanField(default=True)),
                ("is_on_shift", models.BooleanField(db_index=True, default=False)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="dispatcher_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["assigned_zone", "is_on_shift"], name="accounts_di_assigne_718dac_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("email_enabled", models.BooleanField(default=True)),
                ("sms_enabled", models.BooleanField(default=False)),
                ("push_enabled", models.BooleanField(default=True)),
                ("shipment_updates", models.BooleanField(default=True)),
                ("payment_updates", models.BooleanField(default=True)),
                ("marketing_updates", models.BooleanField(default=False)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preference", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["email_enabled", "push_enabled"], name="accounts_no_email__d1b293_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="UserSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("refresh_jti", models.CharField(db_index=True, max_length=255, unique=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("device_name", models.CharField(blank=True, max_length=255)),
                ("last_seen_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user", "revoked_at"], name="accounts_us_user_id_851446_idx"),
                    models.Index(fields=["user", "last_seen_at"], name="accounts_us_user_id_c09da0_idx"),
                ],
            },
        ),
    ]
