from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    role = None

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == self.role
        )


class IsCustomer(RolePermission):
    role = "customer"


class IsRider(RolePermission):
    role = "rider"


class IsDispatcher(RolePermission):
    role = "dispatcher"


class IsAdmin(RolePermission):
    role = "admin"


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", obj)
        return bool(request.user.role == "admin" or owner == request.user)
