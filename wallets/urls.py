from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TransactionViewSet, WalletViewSet

router = DefaultRouter()
router.register("wallets", WalletViewSet, basename="wallet")
router.register("transactions", TransactionViewSet, basename="transaction")

urlpatterns = [path("", include(router.urls))]
