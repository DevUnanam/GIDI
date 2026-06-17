from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Address
from riders.models import RiderProfile
from tracking.models import TrackingEvent

from .models import DeliveryProof, Shipment, ShipmentItem, ShipmentStatus
from .services import hash_otp

User = get_user_model()


class ShipmentWorkflowTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer",
            email="customer@gidi.test",
            password="StrongPass123!",
            role=User.Role.CUSTOMER,
        )
        self.dispatcher = User.objects.create_user(
            username="dispatcher",
            email="dispatcher@gidi.test",
            password="StrongPass123!",
            role=User.Role.DISPATCHER,
        )
        self.rider_user = User.objects.create_user(
            username="rider",
            email="rider@gidi.test",
            password="StrongPass123!",
            role=User.Role.RIDER,
        )
        self.rider = RiderProfile.objects.create(
            user=self.rider_user,
            license_number="RID-P3-001",
            is_approved=True,
        )
        self.pickup = Address.objects.create(
            user=self.customer,
            label="Pickup",
            contact_name="Sender",
            contact_phone="+2348010000001",
            address_line_1="1 Pickup Road",
            city="Lagos",
            state="Lagos",
        )
        self.dropoff = Address.objects.create(
            user=self.customer,
            label="Dropoff",
            contact_name="Receiver",
            contact_phone="+2348010000002",
            address_line_1="2 Dropoff Road",
            city="Lagos",
            state="Lagos",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

    def create_shipment(self):
        self.authenticate(self.customer)
        response = self.client.post(
            reverse("shipment-list"),
            {
                "pickup_address": self.pickup.id,
                "dropoff_address": self.dropoff.id,
                "receiver_name": "Receiver One",
                "receiver_phone": "+2348010000002",
                "package_type": Shipment.PackageType.PARCEL,
                "package_description": "Books and documents",
                "package_weight": "2.50",
                "package_value": "15000.00",
                "delivery_notes": "Call on arrival",
                "service_level": Shipment.ServiceLevel.STANDARD,
                "items": [
                    {
                        "name": "Book pack",
                        "description": "Two books",
                        "quantity": 1,
                        "weight_kg": "2.50",
                        "declared_value": "15000.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Shipment.objects.get(id=response.data["id"])

    def test_customer_can_create_view_cancel_and_list_history(self):
        shipment = self.create_shipment()

        self.assertTrue(shipment.tracking_number.startswith("GDI"))
        self.assertEqual(shipment.status, Shipment.Status.PENDING)
        self.assertEqual(shipment.delivery_fee, Decimal("2125.0000"))
        self.assertTrue(ShipmentItem.objects.filter(shipment=shipment).exists())
        self.assertTrue(ShipmentStatus.objects.filter(shipment=shipment, status=Shipment.Status.PENDING).exists())
        self.assertTrue(TrackingEvent.objects.filter(shipment=shipment, event_type=Shipment.Status.PENDING).exists())

        detail_response = self.client.get(reverse("shipment-detail", kwargs={"pk": shipment.id}))
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["receiver_name"], "Receiver One")

        cancel_response = self.client.post(
            reverse("shipment-cancel", kwargs={"pk": shipment.id}),
            {"notes": "Customer no longer needs dispatch."},
            format="json",
        )
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, Shipment.Status.CANCELLED)

        history_response = self.client.get(reverse("shipment-shipment-history"))
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)

    def test_dispatcher_assigns_and_reassigns_rider(self):
        shipment = self.create_shipment()
        self.authenticate(self.dispatcher)

        assign_response = self.client.post(
            reverse("shipment-assign-rider", kwargs={"pk": shipment.id}),
            {"rider_id": self.rider.id, "notes": "Assign to closest rider."},
            format="json",
        )
        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)
        shipment.refresh_from_db()
        self.assertEqual(shipment.rider_id, self.rider.id)
        self.assertEqual(shipment.dispatcher_id, self.dispatcher.id)
        self.assertEqual(shipment.status, Shipment.Status.ASSIGNED)

        second_rider_user = User.objects.create_user(
            username="rider2",
            email="rider2@gidi.test",
            password="StrongPass123!",
            role=User.Role.RIDER,
        )
        second_rider = RiderProfile.objects.create(
            user=second_rider_user,
            license_number="RID-P3-002",
            is_approved=True,
        )
        reassign_response = self.client.post(
            reverse("shipment-reassign-rider", kwargs={"pk": shipment.id}),
            {"rider_id": second_rider.id},
            format="json",
        )
        self.assertEqual(reassign_response.status_code, status.HTTP_200_OK)
        shipment.refresh_from_db()
        self.assertEqual(shipment.rider_id, second_rider.id)

    def test_rider_accepts_updates_status_and_submits_delivery_proof(self):
        shipment = self.create_shipment()
        shipment.rider = self.rider
        shipment.dispatcher = self.dispatcher
        shipment.status = Shipment.Status.ASSIGNED
        shipment.delivery_otp_hash = hash_otp("123456")
        shipment.delivery_otp_expires_at = timezone.now() + timezone.timedelta(hours=1)
        shipment.save()

        self.authenticate(self.rider_user)
        accept_response = self.client.post(reverse("shipment-accept-delivery", kwargs={"pk": shipment.id}), {}, format="json")
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)

        update_response = self.client.post(
            reverse("shipment-update-delivery-status", kwargs={"pk": shipment.id}),
            {"status": Shipment.Status.IN_TRANSIT, "notes": "Package is moving."},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        proof_response = self.client.post(
            reverse("shipment-delivery-proof", kwargs={"pk": shipment.id}),
            {
                "otp": "123456",
                "receiver_name": "Receiver One",
                "receiver_phone": "+2348010000002",
                "signature": "data:image/svg+xml;base64,PHN2Zy8+",
                "notes": "Handed over successfully.",
            },
            format="multipart",
        )
        self.assertEqual(proof_response.status_code, status.HTTP_201_CREATED)
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, Shipment.Status.DELIVERED)
        self.assertTrue(DeliveryProof.objects.filter(shipment=shipment, otp_verified=True).exists())

        timeline_response = self.client.get(reverse("shipment-timeline", kwargs={"pk": shipment.id}))
        self.assertEqual(timeline_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(timeline_response.data["statuses"]), 3)

    def test_rider_can_reject_assigned_delivery(self):
        shipment = self.create_shipment()
        shipment.rider = self.rider
        shipment.dispatcher = self.dispatcher
        shipment.status = Shipment.Status.ASSIGNED
        shipment.save()

        self.authenticate(self.rider_user)
        response = self.client.post(
            reverse("shipment-reject-delivery", kwargs={"pk": shipment.id}),
            {"notes": "Vehicle issue."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        shipment.refresh_from_db()
        self.assertIsNone(shipment.rider_id)
        self.assertEqual(shipment.status, Shipment.Status.PENDING)
