from rest_framework.permissions import BasePermission


class CanAccessTrackingEvent(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        shipment = obj.shipment
        if user.role in {"admin", "dispatcher"}:
            return True
        if shipment.customer_id == user.id:
            return True
        return bool(shipment.rider and shipment.rider.user_id == user.id)
