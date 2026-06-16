from rest_framework import permissions, viewsets

from .models import Transaction, Wallet
from .permissions import IsWalletOwnerOrAdmin
from .serializers import TransactionSerializer, WalletSerializer


class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated, IsWalletOwnerOrAdmin]

    def get_queryset(self):
        queryset = Wallet.objects.select_related("user").prefetch_related("transactions")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsWalletOwnerOrAdmin]

    def get_queryset(self):
        queryset = Transaction.objects.select_related("wallet", "wallet__user", "shipment")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(wallet__user=self.request.user)
