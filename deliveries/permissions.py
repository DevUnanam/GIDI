from rest_framework.permissions import BasePermission


class CanAccessShipment(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in {"admin", "dispatcher"}:
            return True
        if obj.customer_id == user.id:
            return True
        return bool(obj.rider and obj.rider.user_id == user.id)
