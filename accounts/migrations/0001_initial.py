# Generated for GIDI Phase 1.
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("phone_number", models.CharField(blank=True, max_length=16, null=True, unique=True, validators=[django.core.validators.RegexValidator(message="Enter a valid international phone number.", regex="^\\+?[1-9]\\d{7,14}$")])),
                ("role", models.CharField(choices=[("customer", "Customer"), ("rider", "Rider"), ("dispatcher", "Dispatcher"), ("admin", "Admin")], db_index=True, default="customer", max_length=20)),
                ("is_verified", models.BooleanField(default=False)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["role", "is_active"], name="accounts_us_role_6cf9de_idx"),
                    models.Index(fields=["email", "role"], name="accounts_us_email_f04141_idx"),
                ],
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Address",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("label", models.CharField(max_length=80)),
                ("contact_name", models.CharField(max_length=150)),
                ("contact_phone", models.CharField(max_length=16, validators=[django.core.validators.RegexValidator(message="Enter a valid international phone number.", regex="^\\+?[1-9]\\d{7,14}$")])),
                ("address_line_1", models.CharField(max_length=255)),
                ("address_line_2", models.CharField(blank=True, max_length=255)),
                ("city", models.CharField(db_index=True, max_length=80)),
                ("state", models.CharField(db_index=True, max_length=80)),
                ("country", models.CharField(default="Nigeria", max_length=80)),
                ("postal_code", models.CharField(blank=True, max_length=20)),
                ("latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("is_default", models.BooleanField(default=False)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="addresses", to="accounts.user")),
            ],
            options={
                "verbose_name_plural": "addresses",
                "indexes": [
                    models.Index(fields=["user", "is_default"], name="accounts_ad_user_id_8cf5a2_idx"),
                    models.Index(fields=["city", "state"], name="accounts_ad_city_8b39ba_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(fields=("user", "label"), name="unique_address_label_per_user"),
                ],
            },
        ),
        migrations.CreateModel(
            name="CustomerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("loyalty_points", models.PositiveIntegerField(default=0)),
                ("default_address", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="default_for_customers", to="accounts.address")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="customer_profile", to="accounts.user")),
            ],
            options={
                "indexes": [
                    models.Index(fields=["loyalty_points"], name="accounts_cu_loyalty_6e4269_idx"),
                ],
            },
        ),
    ]
