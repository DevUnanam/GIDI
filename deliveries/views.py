from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from tracking.serializers import TrackingEventSerializer

from .models import DeliveryProof, Shipment, ShipmentItem, ShipmentStatus
from .permissions import CanAccessShipment, CanCreateShipment, IsAssignedRider, IsDispatcherOrAdmin
from .serializers import (
    AssignRiderSerializer,
    CancelShipmentSerializer,
    DeliveryProofCreateSerializer,
    DeliveryProofSerializer,
    ReassignRiderSerializer,
    RiderDecisionSerializer,
    ShipmentItemSerializer,
    ShipmentListSerializer,
    ShipmentSerializer,
    ShipmentStatusSerializer,
    ShipmentStatusUpdateSerializer,
)


class ShipmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanCreateShipment, CanAccessShipment]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "tracking_number",
        "recipient_name",
        "recipient_phone",
        "package_description",
        "customer__email",
        "rider__user__email",
    ]
    ordering_fields = ["created_at", "updated_at", "status", "delivery_fee", "package_weight_kg"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ShipmentListSerializer
        return ShipmentSerializer

    def get_queryset(self):
        queryset = Shipment.objects.select_related(
            "customer",
            "rider",
            "rider__user",
            "dispatcher",
            "pickup_address",
            "dropoff_address",
        ).prefetch_related("items", "status_history", "tracking_events")

        user = self.request.user
        if user.role in {"admin", "dispatcher"}:
            scoped = queryset
        elif user.role == "rider":
            scoped = queryset.filter(rider__user=user)
        else:
            scoped = queryset.filter(customer=user)

        status_filter = self.request.query_params.get("status")
        package_type = self.request.query_params.get("package_type")
        rider_id = self.request.query_params.get("rider")
        created_from = self.request.query_params.get("created_from")
        created_to = self.request.query_params.get("created_to")
        history = self.request.query_params.get("history")

        if status_filter:
            scoped = scoped.filter(status=status_filter)
        if package_type:
            scoped = scoped.filter(package_type=package_type)
        if rider_id:
            scoped = scoped.filter(rider_id=rider_id)
        if created_from:
            scoped = scoped.filter(created_at__date__gte=created_from)
        if created_to:
            scoped = scoped.filter(created_at__date__lte=created_to)
        if history == "true":
            scoped = scoped.filter(status__in=[
                Shipment.Status.DELIVERED,
                Shipment.Status.FAILED,
                Shipment.Status.CANCELLED,
                Shipment.Status.RETURNED,
            ])
        return scoped

    @extend_schema(request=CancelShipmentSerializer, responses=ShipmentSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        shipment = self.get_object()
        serializer = CancelShipmentSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        shipment = serializer.save()
        return Response(ShipmentSerializer(shipment, context={"request": request}).data)

    @extend_schema(request=AssignRiderSerializer, responses=ShipmentSerializer)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsDispatcherOrAdmin])
    def assign_rider(self, request, pk=None):
        shipment = self.get_object()
        serializer = AssignRiderSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        shipment = serializer.save()
        return Response(ShipmentSerializer(shipment, context={"request": request}).data)

    @extend_schema(request=ReassignRiderSerializer, responses=ShipmentSerializer)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsDispatcherOrAdmin])
    def reassign_rider(self, request, pk=None):
        shipment = self.get_object()
        serializer = ReassignRiderSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        shipment = serializer.save()
        return Response(ShipmentSerializer(shipment, context={"request": request}).data)

    @extend_schema(request=ShipmentStatusUpdateSerializer, responses=ShipmentSerializer)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsDispatcherOrAdmin])
    def update_status(self, request, pk=None):
        shipment = self.get_object()
        serializer = ShipmentStatusUpdateSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        shipment = serializer.save()
        return Response(ShipmentSerializer(shipment, context={"request": request}).data)

    @extend_schema(request=RiderDecisionSerializer, responses=ShipmentSerializer)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAssignedRider])
    def accept_delivery(self, request, pk=None):
        shipment = self.get_object()
        serializer = RiderDecisionSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        shipment = serializer.accept()
        return Response(ShipmentSerializer(shipment, context={"request": request}).data)

    @extend_schema(request=RiderDecisionSerializer, responses=ShipmentSerializer)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAssignedRider])
    def reject_delivery(self, request, pk=None):
        shipment = self.get_object()
        serializer = RiderDecisionSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        shipment = serializer.reject()
        return Response(ShipmentSerializer(shipment, context={"request": request}).data)

    @extend_schema(request=ShipmentStatusUpdateSerializer, responses=ShipmentSerializer)
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAssignedRider])
    def update_delivery_status(self, request, pk=None):
        shipment = self.get_object()
        allowed = {
            Shipment.Status.PICKED_UP,
            Shipment.Status.IN_TRANSIT,
            Shipment.Status.NEAR_DESTINATION,
            Shipment.Status.FAILED,
            Shipment.Status.RETURNED,
        }
        serializer = ShipmentStatusUpdateSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["status"] not in allowed:
            return Response({"detail": "Rider cannot set this status with this endpoint."}, status=status.HTTP_400_BAD_REQUEST)
        shipment = serializer.save()
        return Response(ShipmentSerializer(shipment, context={"request": request}).data)

    @extend_schema(request=DeliveryProofCreateSerializer, responses=DeliveryProofSerializer)
    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[permissions.IsAuthenticated, IsAssignedRider],
    )
    def delivery_proof(self, request, pk=None):
        shipment = self.get_object()
        serializer = DeliveryProofCreateSerializer(data=request.data, context={"request": request, "shipment": shipment})
        serializer.is_valid(raise_exception=True)
        proof = serializer.save()
        return Response(DeliveryProofSerializer(proof, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        shipment = self.get_object()
        return Response(
            {
                "statuses": ShipmentStatusSerializer(shipment.status_history.order_by("created_at"), many=True).data,
                "tracking_events": TrackingEventSerializer(shipment.tracking_events.order_by("created_at"), many=True).data,
            }
        )

    @action(detail=False, methods=["get"], url_path="history")
    def shipment_history(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                Q(status=Shipment.Status.DELIVERED)
                | Q(status=Shipment.Status.FAILED)
                | Q(status=Shipment.Status.CANCELLED)
                | Q(status=Shipment.Status.RETURNED)
            )
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ShipmentListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = ShipmentListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class ShipmentItemViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ShipmentItem.objects.select_related("shipment", "shipment__customer", "shipment__rider")
        user = self.request.user
        if user.role in {"admin", "dispatcher"}:
            return queryset
        if user.role == "rider":
            return queryset.filter(shipment__rider__user=user)
        return queryset.filter(shipment__customer=user)


class ShipmentStatusViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShipmentStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["shipment__tracking_number", "notes", "changed_by__email"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = ShipmentStatus.objects.select_related("shipment", "changed_by")
        user = self.request.user
        if user.role in {"admin", "dispatcher"}:
            return queryset
        if user.role == "rider":
            return queryset.filter(shipment__rider__user=user)
        return queryset.filter(shipment__customer=user)


class DeliveryProofViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeliveryProofSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = DeliveryProof.objects.select_related("shipment", "verified_by")
        user = self.request.user
        if user.role in {"admin", "dispatcher"}:
            return queryset
        if user.role == "rider":
            return queryset.filter(shipment__rider__user=user)
        return queryset.filter(shipment__customer=user)
