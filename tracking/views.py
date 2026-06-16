from rest_framework import permissions, viewsets

from .models import TrackingEvent
from .permissions import CanAccessTrackingEvent
from .serializers import TrackingEventSerializer


class TrackingEventViewSet(viewsets.ModelViewSet):
    serializer_class = TrackingEventSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessTrackingEvent]

    def get_queryset(self):
        queryset = TrackingEvent.objects.select_related("shipment", "shipment__customer", "shipment__rider", "recorded_by")
        user = self.request.user
        if user.role in {"admin", "dispatcher"}:
            return queryset
        if user.role == "rider":
            return queryset.filter(shipment__rider__user=user)
        return queryset.filter(shipment__customer=user)

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
