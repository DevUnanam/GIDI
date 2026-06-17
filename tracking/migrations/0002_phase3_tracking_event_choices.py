# Generated for GIDI Phase 3.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tracking", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="trackingevent",
            name="event_type",
            field=models.CharField(choices=[("created", "Created"), ("pending", "Pending"), ("assigned", "Assigned"), ("accepted", "Accepted"), ("pickup_started", "Pickup started"), ("picked_up", "Picked up"), ("in_transit", "In transit"), ("near_destination", "Near destination"), ("location_update", "Location update"), ("delivery_attempted", "Delivery attempted"), ("delivered", "Delivered"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("returned", "Returned")], db_index=True, max_length=30),
        ),
    ]
