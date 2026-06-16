from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RiderProfileViewSet, VehicleViewSet

router = DefaultRouter()
router.register("profiles", RiderProfileViewSet, basename="rider-profile")
router.register("vehicles", VehicleViewSet, basename="vehicle")

urlpatterns = [path("", include(router.urls))]
