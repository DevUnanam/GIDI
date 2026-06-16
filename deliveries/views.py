from rest_framework import permissions, viewsets

from .models import Shipment, ShipmentStatus
from .permissions import CanAccessShipment
from .serializers import ShipmentSerializer, ShipmentStatusSerializer


class ShipmentViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessShipment]

    def get_queryset(self):
        queryset = Shipment.objects.select_related(
            "customer",
            "rider",
            "rider__user",
            "pickup_address",
            "dropoff_address",
        ).prefetch_related("status_history")
        user = self.request.user
        if user.role in {"admin", "dispatcher"}:
            return queryset
        if user.role == "rider":
            return queryset.filter(rider__user=user)
        return queryset.filter(customer=user)


class ShipmentStatusViewSet(viewsets.ModelViewSet):
    serializer_class = ShipmentStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ShipmentStatus.objects.select_related("shipment", "changed_by")
        user = self.request.user
        if user.role in {"admin", "dispatcher"}:
            return queryset
        if user.role == "rider":
            return queryset.filter(shipment__rider__user=user)
        return queryset.filter(shipment__customer=user)

    def perform_create(self, serializer):
        serializer.save(changed_by=self.request.user)
