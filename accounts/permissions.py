from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", obj)
        return bool(request.user.role == "admin" or owner == request.user)
