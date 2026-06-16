from rest_framework import serializers

from .models import RiderProfile, Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class RiderProfileSerializer(serializers.ModelSerializer):
    vehicles = VehicleSerializer(many=True, read_only=True)

    class Meta:
        model = RiderProfile
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
