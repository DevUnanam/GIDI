from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

from riders.models import RiderProfile

from .models import CustomerProfile, DispatcherProfile, NotificationPreference, UserSession

User = get_user_model()


@dataclass(frozen=True)
class TokenBundle:
    access: str
    refresh: str
    refresh_jti: str
    expires_at: datetime


def issue_tokens(user: User) -> TokenBundle:
    refresh = RefreshToken.for_user(user)
    return TokenBundle(
        access=str(refresh.access_token),
        refresh=str(refresh),
        refresh_jti=str(refresh["jti"]),
        expires_at=timezone.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
    )


def create_user_session(user: User, token_bundle: TokenBundle, request) -> UserSession:
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")
    device_name = user_agent[:255] if user_agent else "Unknown device"
    return UserSession.objects.create(
        user=user,
        refresh_jti=token_bundle.refresh_jti,
        ip_address=ip_address or None,
        user_agent=user_agent,
        device_name=device_name,
        expires_at=token_bundle.expires_at,
    )


def revoke_session(session: UserSession) -> None:
    if session.revoked_at is None:
        session.revoked_at = timezone.now()
        session.save(update_fields=["revoked_at", "updated_at"])


def blacklist_refresh_token(refresh_token: str) -> None:
    RefreshToken(refresh_token).blacklist()


def send_verification_email(user: User) -> None:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verification_path = f"/api/auth/email/verify/?uid={uid}&token={token}"
    send_mail(
        "Verify your GIDI account",
        f"Use this link to verify your email address: {verification_path}",
        None,
        [user.email],
        fail_silently=False,
    )


@transaction.atomic
def register_user(*, role: str, password: str, profile_data: dict | None = None, **user_data) -> User:
    user = User(**user_data, role=role)
    user.set_password(password)
    user.full_clean(exclude=["password"])
    user.save()
    NotificationPreference.objects.create(user=user)

    profile_data = profile_data or {}
    if role == User.Role.CUSTOMER:
        CustomerProfile.objects.create(user=user, **profile_data)
    elif role == User.Role.RIDER:
        RiderProfile.objects.create(user=user, **profile_data)
    elif role == User.Role.DISPATCHER:
        DispatcherProfile.objects.create(user=user, **profile_data)

    send_verification_email(user)
    return user
