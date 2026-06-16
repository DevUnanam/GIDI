from rest_framework import serializers

from .models import Shipment, ShipmentStatus


class ShipmentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentStatus
        fields = "__all__"
        read_only_fields = ["changed_by", "created_at", "updated_at"]


class ShipmentSerializer(serializers.ModelSerializer):
    status_history = ShipmentStatusSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = "__all__"
        read_only_fields = ["customer", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        shipment = Shipment.objects.create(customer=request.user, **validated_data)
        ShipmentStatus.objects.create(
            shipment=shipment,
            status=shipment.status,
            changed_by=request.user,
            notes="Shipment created.",
        )
        return shipment
