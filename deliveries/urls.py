from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DeliveryProofViewSet, ShipmentItemViewSet, ShipmentStatusViewSet, ShipmentViewSet

router = DefaultRouter()
router.register("shipments", ShipmentViewSet, basename="shipment")
router.register("items", ShipmentItemViewSet, basename="shipment-item")
router.register("statuses", ShipmentStatusViewSet, basename="shipment-status")
router.register("proofs", DeliveryProofViewSet, basename="delivery-proof")

urlpatterns = [path("", include(router.urls))]
