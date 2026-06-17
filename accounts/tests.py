from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from riders.models import RiderProfile

from .models import CustomerProfile, DispatcherProfile, NotificationPreference, UserSession

User = get_user_model()


class AuthenticationTests(APITestCase):
    def test_register_customer_creates_profile_preferences_session_and_tokens(self):
        response = self.client.post(
            reverse("register_customer"),
            {
                "username": "ada",
                "email": "ada@gidi.test",
                "password": "StrongPass123!",
                "first_name": "Ada",
                "last_name": "Okafor",
                "phone_number": "+2348011111111",
                "marketing_opt_in": True,
            },
            format="json",
            HTTP_USER_AGENT="pytest browser",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        user = User.objects.get(email="ada@gidi.test")
        self.assertEqual(user.role, User.Role.CUSTOMER)
        self.assertTrue(CustomerProfile.objects.filter(user=user, marketing_opt_in=True).exists())
        self.assertTrue(NotificationPreference.objects.filter(user=user).exists())
        self.assertTrue(UserSession.objects.filter(user=user, revoked_at__isnull=True).exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_register_rider_creates_rider_profile(self):
        response = self.client.post(
            reverse("register_rider"),
            {
                "username": "rider1",
                "email": "rider@gidi.test",
                "password": "StrongPass123!",
                "phone_number": "+2348022222222",
                "license_number": "RID-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="rider@gidi.test")
        self.assertEqual(user.role, User.Role.RIDER)
        self.assertTrue(RiderProfile.objects.filter(user=user, license_number="RID-123").exists())

    def test_register_dispatcher_creates_dispatcher_profile(self):
        response = self.client.post(
            reverse("register_dispatcher"),
            {
                "username": "dispatch1",
                "email": "dispatch@gidi.test",
                "password": "StrongPass123!",
                "phone_number": "+2348033333333",
                "employee_id": "DSP-001",
                "assigned_zone": "Lagos Island",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="dispatch@gidi.test")
        self.assertEqual(user.role, User.Role.DISPATCHER)
        self.assertTrue(DispatcherProfile.objects.filter(user=user, employee_id="DSP-001").exists())

    def test_login_tracks_session_and_logout_revokes_it(self):
        user = User.objects.create_user(
            username="loginuser",
            email="login@gidi.test",
            password="StrongPass123!",
            role=User.Role.CUSTOMER,
        )
        CustomerProfile.objects.create(user=user)
        NotificationPreference.objects.create(user=user)

        login_response = self.client.post(
            reverse("login"),
            {"email": "login@gidi.test", "password": "StrongPass123!"},
            format="json",
            HTTP_USER_AGENT="pytest browser",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        session = UserSession.objects.get(user=user, revoked_at__isnull=True)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        logout_response = self.client.post(
            reverse("logout"),
            {"refresh": login_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)
        session.refresh_from_db()
        self.assertIsNotNone(session.revoked_at)

    def test_email_verification_marks_user_verified(self):
        user = User.objects.create_user(
            username="verifyme",
            email="verify@gidi.test",
            password="StrongPass123!",
            role=User.Role.CUSTOMER,
        )
        refresh = RefreshToken.for_user(user)
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        response = self.client.post(
            reverse("email_verify"),
            {
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)


class ProfileAndSessionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profile",
            email="profile@gidi.test",
            password="StrongPass123!",
            role=User.Role.CUSTOMER,
        )
        CustomerProfile.objects.create(user=self.user)
        NotificationPreference.objects.create(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

    def test_get_and_update_profile(self):
        get_response = self.client.get(reverse("profile"))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            reverse("profile"),
            {
                "user": {"first_name": "Updated"},
                "customer_profile": {"marketing_opt_in": True},
            },
            format="json",
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.user.customer_profile.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertTrue(self.user.customer_profile.marketing_opt_in)

    def test_update_address_and_set_default(self):
        create_response = self.client.post(
            reverse("address-list"),
            {
                "label": "Home",
                "contact_name": "Profile User",
                "contact_phone": "+2348044444444",
                "address_line_1": "12 Test Street",
                "city": "Lagos",
                "state": "Lagos",
                "country": "Nigeria",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        set_default_response = self.client.post(
            reverse("address-set-default", kwargs={"pk": create_response.data["id"]}),
            format="json",
        )
        self.assertEqual(set_default_response.status_code, status.HTTP_200_OK)
        self.user.customer_profile.refresh_from_db()
        self.assertEqual(self.user.customer_profile.default_address_id, create_response.data["id"])

    def test_logout_device_revokes_session(self):
        session = UserSession.objects.create(
            user=self.user,
            refresh_jti="test-jti",
            device_name="test device",
            expires_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.post(
            reverse("session-logout-device"),
            {"session_id": session.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertIsNotNone(session.revoked_at)
