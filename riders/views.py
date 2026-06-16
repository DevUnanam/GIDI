from rest_framework import permissions, viewsets

from .models import RiderProfile, Vehicle
from .permissions import IsRiderOwnerOrAdmin
from .serializers import RiderProfileSerializer, VehicleSerializer


class RiderProfileViewSet(viewsets.ModelViewSet):
    serializer_class = RiderProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsRiderOwnerOrAdmin]

    def get_queryset(self):
        queryset = RiderProfile.objects.select_related("user").prefetch_related("vehicles")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(user=self.request.user)


class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated, IsRiderOwnerOrAdmin]

    def get_queryset(self):
        queryset = Vehicle.objects.select_related("rider", "rider__user")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(rider__user=self.request.user)
