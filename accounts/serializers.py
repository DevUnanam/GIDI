from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from riders.models import RiderProfile

from .models import Address, CustomerProfile, DispatcherProfile, NotificationPreference, UserSession
from .services import blacklist_refresh_token, register_user, revoke_session

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_verified",
            "avatar",
            "date_joined",
        ]
        read_only_fields = ["id", "role", "is_verified", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "phone_number", "role"]
        read_only_fields = ["id"]

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if user.role == User.Role.CUSTOMER:
            CustomerProfile.objects.get_or_create(user=user)
        return user


class BaseRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "phone_number"]
        read_only_fields = ["id"]

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create_user(self, validated_data, role, profile_data=None):
        password = validated_data.pop("password")
        return register_user(role=role, password=password, profile_data=profile_data, **validated_data)


class CustomerRegistrationSerializer(BaseRegistrationSerializer):
    marketing_opt_in = serializers.BooleanField(required=False, default=False)

    class Meta(BaseRegistrationSerializer.Meta):
        fields = BaseRegistrationSerializer.Meta.fields + ["marketing_opt_in"]

    def create(self, validated_data):
        profile_data = {"marketing_opt_in": validated_data.pop("marketing_opt_in", False)}
        return self.create_user(validated_data, User.Role.CUSTOMER, profile_data)


class RiderRegistrationSerializer(BaseRegistrationSerializer):
    license_number = serializers.CharField(max_length=80)

    class Meta(BaseRegistrationSerializer.Meta):
        fields = BaseRegistrationSerializer.Meta.fields + ["license_number"]

    def create(self, validated_data):
        profile_data = {"license_number": validated_data.pop("license_number")}
        return self.create_user(validated_data, User.Role.RIDER, profile_data)


class DispatcherRegistrationSerializer(BaseRegistrationSerializer):
    employee_id = serializers.CharField(max_length=50)
    assigned_zone = serializers.CharField(max_length=120, required=False, allow_blank=True)

    class Meta(BaseRegistrationSerializer.Meta):
        fields = BaseRegistrationSerializer.Meta.fields + ["employee_id", "assigned_zone"]

    def create(self, validated_data):
        profile_data = {
            "employee_id": validated_data.pop("employee_id"),
            "assigned_zone": validated_data.pop("assigned_zone", ""),
        }
        return self.create_user(validated_data, User.Role.DISPATCHER, profile_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid credentials.") from exc
        authenticated = authenticate(username=user.username, password=attrs["password"])
        if not authenticated:
            raise serializers.ValidationError("Invalid credentials.")
        if not authenticated.is_active:
            raise serializers.ValidationError("This account is disabled.")
        attrs["user"] = authenticated
        return attrs


class TokenResponseSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    access = serializers.CharField()
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        self.token = RefreshToken(value)
        return value

    def save(self, **kwargs):
        refresh_jti = str(self.token["jti"])
        UserSession.objects.filter(refresh_jti=refresh_jti, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
        self.token.blacklist()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"]
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_path = f"/api/auth/password-reset/confirm/?uid={uid}&token={token}"
        send_mail(
            "Reset your GIDI password",
            f"Use this link to reset your password: {reset_path}",
            None,
            [user.email],
            fail_silently=False,
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError("Invalid password reset link.") from exc
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid password reset token.")
        password_validation.validate_password(attrs["new_password"], user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]


class RiderProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RiderProfile
        fields = "__all__"
        read_only_fields = ["user", "rating", "completed_deliveries", "is_approved", "created_at", "updated_at"]


class DispatcherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DispatcherProfile
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]


class ProfileSerializer(serializers.Serializer):
    user = UserSerializer()
    customer_profile = CustomerProfileSerializer(required=False, allow_null=True)
    rider_profile = RiderProfileSerializer(required=False, allow_null=True)
    dispatcher_profile = DispatcherProfileSerializer(required=False, allow_null=True)
    notification_preference = serializers.SerializerMethodField()

    def get_notification_preference(self, obj):
        preference, _ = NotificationPreference.objects.get_or_create(user=obj["user"])
        return NotificationPreferenceSerializer(preference).data


class AvatarUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["avatar"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]


class UserSessionSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSession
        fields = [
            "id",
            "device_name",
            "ip_address",
            "user_agent",
            "last_seen_at",
            "expires_at",
            "revoked_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields


class LogoutDeviceSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()

    def validate_session_id(self, value):
        request = self.context["request"]
        try:
            self.session = UserSession.objects.get(id=value, user=request.user)
        except UserSession.DoesNotExist as exc:
            raise serializers.ValidationError("Session not found.") from exc
        return value

    def save(self, **kwargs):
        revoke_session(self.session)


class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=uid, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError("Invalid verification link.") from exc
        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid verification token.")
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.is_verified = True
        user.save(update_fields=["is_verified"])


class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        from .services import send_verification_email

        user = User.objects.filter(email__iexact=self.validated_data["email"], is_active=True).first()
        if user and not user.is_verified:
            send_verification_email(user)
