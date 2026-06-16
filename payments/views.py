from rest_framework import permissions, viewsets

from .models import Payment
from .permissions import IsPaymentOwnerOrAdmin
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsPaymentOwnerOrAdmin]

    def get_queryset(self):
        queryset = Payment.objects.select_related("user", "shipment", "wallet_transaction")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(user=self.request.user)
