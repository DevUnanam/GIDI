from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TrackingEventViewSet

router = DefaultRouter()
router.register("events", TrackingEventViewSet, basename="tracking-event")

urlpatterns = [path("", include(router.urls))]
