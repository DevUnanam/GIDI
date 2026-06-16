from rest_framework.permissions import BasePermission


class IsRiderOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        rider = getattr(obj, "rider", obj)
        return getattr(rider, "user_id", None) == request.user.id
