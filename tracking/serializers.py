from rest_framework import serializers

from .models import TrackingEvent


class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = "__all__"
        read_only_fields = ["recorded_by", "created_at", "updated_at"]
