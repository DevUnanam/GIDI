from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from riders.models import RiderProfile
from tracking.serializers import TrackingEventSerializer

from .models import DeliveryProof, Shipment, ShipmentItem, ShipmentStatus
from .services import (
    accept_delivery,
    assign_rider,
    cancel_shipment,
    create_shipment,
    record_delivery_proof,
    reassign_rider,
    reject_delivery,
    update_shipment_status,
)


class ShipmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentItem
        fields = ["id", "name", "description", "quantity", "weight_kg", "declared_value", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ShipmentStatusSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True)

    class Meta:
        model = ShipmentStatus
        fields = ["id", "shipment", "status", "notes", "changed_by", "changed_by_email", "created_at", "updated_at"]
        read_only_fields = ["changed_by", "created_at", "updated_at"]


class DeliveryProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryProof
        fields = [
            "id",
            "shipment",
            "verified_by",
            "receiver_name",
            "receiver_phone",
            "otp_verified",
            "delivery_photo",
            "signature",
            "signed_at",
            "delivered_at",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["verified_by", "otp_verified", "signed_at", "delivered_at", "created_at", "updated_at"]


class ShipmentSerializer(serializers.ModelSerializer):
    items = ShipmentItemSerializer(many=True, required=False)
    status_history = ShipmentStatusSerializer(many=True, read_only=True)
    tracking_events = TrackingEventSerializer(many=True, read_only=True)
    delivery_proof = DeliveryProofSerializer(read_only=True)
    receiver_name = serializers.CharField(source="recipient_name")
    receiver_phone = serializers.CharField(source="recipient_phone")
    package_weight = serializers.DecimalField(source="package_weight_kg", max_digits=8, decimal_places=2)
    estimated_fee = serializers.DecimalField(source="delivery_fee", max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "customer",
            "rider",
            "dispatcher",
            "tracking_number",
            "pickup_address",
            "dropoff_address",
            "receiver_name",
            "receiver_phone",
            "package_type",
            "package_description",
            "package_weight",
            "package_value",
            "delivery_notes",
            "estimated_fee",
            "service_level",
            "status",
            "scheduled_pickup_at",
            "picked_up_at",
            "delivered_at",
            "items",
            "status_history",
            "tracking_events",
            "delivery_proof",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "customer",
            "rider",
            "dispatcher",
            "tracking_number",
            "status",
            "picked_up_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        request = self.context["request"]
        return create_shipment(customer=request.user, items=items, **validated_data)


class ShipmentListSerializer(serializers.ModelSerializer):
    receiver_name = serializers.CharField(source="recipient_name", read_only=True)
    package_weight = serializers.DecimalField(source="package_weight_kg", max_digits=8, decimal_places=2, read_only=True)
    estimated_fee = serializers.DecimalField(source="delivery_fee", max_digits=12, decimal_places=2, read_only=True)
    rider_name = serializers.CharField(source="rider.user.get_full_name", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "tracking_number",
            "customer",
            "rider",
            "rider_name",
            "dispatcher",
            "receiver_name",
            "package_type",
            "package_weight",
            "estimated_fee",
            "status",
            "created_at",
        ]


class AssignRiderSerializer(serializers.Serializer):
    rider_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_rider_id(self, value):
        try:
            self.rider = RiderProfile.objects.select_related("user").get(id=value, is_approved=True)
        except RiderProfile.DoesNotExist as exc:
            raise serializers.ValidationError("Approved rider not found.") from exc
        return value

    def save(self, **kwargs):
        shipment = self.context["shipment"]
        dispatcher = self.context["request"].user
        try:
            return assign_rider(
                shipment=shipment,
                rider=self.rider,
                dispatcher=dispatcher,
                notes=self.validated_data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class ReassignRiderSerializer(AssignRiderSerializer):
    def save(self, **kwargs):
        shipment = self.context["shipment"]
        dispatcher = self.context["request"].user
        try:
            return reassign_rider(
                shipment=shipment,
                rider=self.rider,
                dispatcher=dispatcher,
                notes=self.validated_data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class ShipmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Shipment.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        try:
            return update_shipment_status(
                shipment=self.context["shipment"],
                status=self.validated_data["status"],
                actor=self.context["request"].user,
                notes=self.validated_data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class CancelShipmentSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        try:
            return cancel_shipment(
                shipment=self.context["shipment"],
                actor=self.context["request"].user,
                notes=self.validated_data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class RiderDecisionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)

    def accept(self):
        try:
            return accept_delivery(shipment=self.context["shipment"], rider_user=self.context["request"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    def reject(self):
        try:
            return reject_delivery(
                shipment=self.context["shipment"],
                rider_user=self.context["request"].user,
                notes=self.validated_data.get("notes", ""),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class DeliveryProofCreateSerializer(serializers.Serializer):
    otp = serializers.RegexField(regex=r"^\d{6}$", write_only=True)
    receiver_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    receiver_phone = serializers.CharField(max_length=16, required=False, allow_blank=True)
    delivery_photo = serializers.ImageField(required=False, allow_null=True)
    signature = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        proof_data = {
            "receiver_name": self.validated_data.get("receiver_name", ""),
            "receiver_phone": self.validated_data.get("receiver_phone", ""),
            "delivery_photo": self.validated_data.get("delivery_photo"),
            "signature": self.validated_data.get("signature", ""),
            "notes": self.validated_data.get("notes", ""),
        }
        proof_data = {key: value for key, value in proof_data.items() if value not in (None, "")}
        try:
            return record_delivery_proof(
                shipment=self.context["shipment"],
                actor=self.context["request"].user,
                otp=self.validated_data["otp"],
                proof_data=proof_data,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)


class ShipmentTimelineSerializer(serializers.Serializer):
    statuses = ShipmentStatusSerializer(many=True)
    tracking_events = TrackingEventSerializer(many=True)
