from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ShipmentStatusViewSet, ShipmentViewSet

router = DefaultRouter()
router.register("shipments", ShipmentViewSet, basename="shipment")
router.register("statuses", ShipmentStatusViewSet, basename="shipment-status")

urlpatterns = [path("", include(router.urls))]
