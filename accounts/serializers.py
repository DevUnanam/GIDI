from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Address, CustomerProfile

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
            "date_joined",
        ]
        read_only_fields = ["id", "is_verified", "date_joined"]


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
