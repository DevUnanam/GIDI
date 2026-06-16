from rest_framework.permissions import BasePermission


class IsNotificationOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.role == "admin" or obj.user_id == request.user.id
