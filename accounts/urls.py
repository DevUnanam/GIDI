from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AddressViewSet,
    AvatarUploadView,
    CustomerProfileView,
    LoginView,
    LogoutView,
    MeView,
    NotificationPreferenceView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterCustomerView,
    RegisterDispatcherView,
    RegisterRiderView,
    RegisterView,
    ResendEmailVerificationView,
    UserSessionViewSet,
    VerifyEmailView,
)

router = DefaultRouter()
router.register("addresses", AddressViewSet, basename="address")
router.register("sessions", UserSessionViewSet, basename="session")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register/customer/", RegisterCustomerView.as_view(), name="register_customer"),
    path("register/rider/", RegisterRiderView.as_view(), name="register_rider"),
    path("register/dispatcher/", RegisterDispatcherView.as_view(), name="register_dispatcher"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("email/verify/", VerifyEmailView.as_view(), name="email_verify"),
    path("email/resend-verification/", ResendEmailVerificationView.as_view(), name="email_resend_verification"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/avatar/", AvatarUploadView.as_view(), name="profile_avatar"),
    path("profile/notification-preferences/", NotificationPreferenceView.as_view(), name="notification_preferences"),
    path("customer-profile/", CustomerProfileView.as_view(), name="customer_profile"),
    path("", include(router.urls)),
]
