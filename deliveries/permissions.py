from rest_framework.permissions import BasePermission


class CanAccessShipment(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role in {"admin", "dispatcher"}:
            return True
        if obj.customer_id == user.id:
            return True
        return bool(obj.rider and obj.rider.user_id == user.id)


class CanCreateShipment(BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return bool(request.user and request.user.is_authenticated and request.user.role == "customer")
        return True


class IsDispatcherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in {"dispatcher", "admin"})


class IsAssignedRider(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and obj.rider and obj.rider.user_id == request.user.id)
