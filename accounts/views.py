from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Address, CustomerProfile, DispatcherProfile, NotificationPreference, UserSession
from .permissions import IsSelfOrAdmin
from .serializers import (
    AddressSerializer,
    AvatarUploadSerializer,
    CustomerProfileSerializer,
    CustomerRegistrationSerializer,
    DispatcherProfileSerializer,
    DispatcherRegistrationSerializer,
    EmailVerificationSerializer,
    LoginSerializer,
    LogoutDeviceSerializer,
    LogoutSerializer,
    NotificationPreferenceSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ResendEmailVerificationSerializer,
    RiderProfileSerializer,
    RiderRegistrationSerializer,
    UserSessionSerializer,
    UserSerializer,
)
from .services import create_user_session, issue_tokens


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


def token_payload(user, request=None):
    token_bundle = issue_tokens(user)
    if request is not None:
        create_user_session(user, token_bundle, request)
    return {
        "user": UserSerializer(user).data,
        "access": token_bundle.access,
        "refresh": token_bundle.refresh,
    }


class RegisterView(generics.CreateAPIView):
    serializer_class = CustomerRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(token_payload(user, request), status=status.HTTP_201_CREATED)


class RegisterCustomerView(RegisterView):
    serializer_class = CustomerRegistrationSerializer


class RegisterRiderView(RegisterView):
    serializer_class = RiderRegistrationSerializer


class RegisterDispatcherView(RegisterView):
    serializer_class = DispatcherRegistrationSerializer


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(token_payload(serializer.validated_data["user"], request))


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "If the email exists, reset instructions have been sent."})


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset successful."})


class VerifyEmailView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Email verified successfully."})


class ResendEmailVerificationView(generics.GenericAPIView):
    serializer_class = ResendEmailVerificationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "If the account exists and is unverified, a verification email has been sent."})


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        user = self.request.user
        return {
            "user": user,
            "customer_profile": getattr(user, "customer_profile", None),
            "rider_profile": getattr(user, "rider_profile", None),
            "dispatcher_profile": getattr(user, "dispatcher_profile", None),
        }

    def update(self, request, *args, **kwargs):
        user_serializer = UserSerializer(request.user, data=request.data.get("user", {}), partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        if request.user.role == "customer":
            profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
            serializer = CustomerProfileSerializer(profile, data=request.data.get("customer_profile", {}), partial=True)
        elif request.user.role == "rider":
            serializer = RiderProfileSerializer(request.user.rider_profile, data=request.data.get("rider_profile", {}), partial=True)
        elif request.user.role == "dispatcher":
            serializer = DispatcherProfileSerializer(request.user.dispatcher_profile, data=request.data.get("dispatcher_profile", {}), partial=True)
        else:
            serializer = None

        if serializer is not None:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(self.get_serializer(self.get_object()).data)


class AvatarUploadView(generics.UpdateAPIView):
    serializer_class = AvatarUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsSelfOrAdmin]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Address.objects.select_related("user")
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        address = self.get_object()
        Address.objects.filter(user=address.user).update(is_default=False)
        address.is_default = True
        address.save(update_fields=["is_default", "updated_at"])
        CustomerProfile.objects.filter(user=address.user).update(default_address=address)
        return Response(self.get_serializer(address).data)


class CustomerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer

    def get_object(self):
        profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
        return profile


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        preference, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return preference


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSessionSerializer

    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user, revoked_at__isnull=True).order_by("-last_seen_at")

    @extend_schema(request=LogoutDeviceSerializer, responses={200: None})
    @action(detail=False, methods=["post"], url_path="logout-device")
    def logout_device(self, request):
        serializer = LogoutDeviceSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Device session logged out."})
