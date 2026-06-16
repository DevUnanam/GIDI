from rest_framework.permissions import BasePermission


class IsWalletOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        wallet = getattr(obj, "wallet", obj)
        return wallet.user_id == request.user.id
