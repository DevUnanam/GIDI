import hashlib
import secrets
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from riders.models import RiderProfile
from tracking.models import TrackingEvent

from .models import DeliveryProof, Shipment, ShipmentStatus

User = get_user_model()

TRACKING_PREFIX = "GDI"
TERMINAL_STATUSES = {
    Shipment.Status.DELIVERED,
    Shipment.Status.FAILED,
    Shipment.Status.CANCELLED,
    Shipment.Status.RETURNED,
}


def generate_tracking_number() -> str:
    while True:
        candidate = f"{TRACKING_PREFIX}{timezone.now():%Y%m%d}{secrets.randbelow(10**8):08d}"
        if not Shipment.objects.filter(tracking_number=candidate).exists():
            return candidate


def estimate_delivery_fee(package_weight_kg: Decimal, service_level: str) -> Decimal:
    base_fee = Decimal("1500.00")
    weight_fee = Decimal(package_weight_kg) * Decimal("250.00")
    multiplier = {
        Shipment.ServiceLevel.STANDARD: Decimal("1.00"),
        Shipment.ServiceLevel.EXPRESS: Decimal("1.50"),
        Shipment.ServiceLevel.SAME_DAY: Decimal("2.00"),
    }.get(service_level, Decimal("1.00"))
    return (base_fee + weight_fee) * multiplier


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def generate_delivery_otp(shipment: Shipment) -> str:
    otp = f"{secrets.randbelow(10**6):06d}"
    shipment.delivery_otp_hash = hash_otp(otp)
    shipment.delivery_otp_expires_at = timezone.now() + timezone.timedelta(hours=24)
    shipment.save(update_fields=["delivery_otp_hash", "delivery_otp_expires_at", "updated_at"])
    return otp


def verify_delivery_otp(shipment: Shipment, otp: str) -> bool:
    if not shipment.delivery_otp_hash or not shipment.delivery_otp_expires_at:
        return False
    if shipment.delivery_otp_expires_at < timezone.now():
        return False
    return secrets.compare_digest(shipment.delivery_otp_hash, hash_otp(otp))


def create_status_event(shipment: Shipment, status: str, actor=None, notes: str = "") -> ShipmentStatus:
    status_record = ShipmentStatus.objects.create(
        shipment=shipment,
        status=status,
        changed_by=actor,
        notes=notes,
    )
    TrackingEvent.objects.create(
        shipment=shipment,
        event_type=status,
        message=notes or f"Shipment status changed to {shipment.get_status_display()}.",
        recorded_by=actor,
        metadata={"status": status},
    )
    return status_record


@transaction.atomic
def create_shipment(*, customer, items=None, **shipment_data) -> Shipment:
    shipment_data.setdefault("tracking_number", generate_tracking_number())
    shipment_data.setdefault(
        "delivery_fee",
        estimate_delivery_fee(shipment_data["package_weight_kg"], shipment_data.get("service_level", Shipment.ServiceLevel.STANDARD)),
    )
    shipment = Shipment.objects.create(customer=customer, **shipment_data)
    for item in items or []:
        shipment.items.create(**item)
    create_status_event(shipment, Shipment.Status.PENDING, customer, "Shipment booking created.")
    generate_delivery_otp(shipment)
    return shipment


@transaction.atomic
def assign_rider(*, shipment: Shipment, rider: RiderProfile, dispatcher: User, notes: str = "") -> Shipment:
    if dispatcher.role not in {"dispatcher", "admin"}:
        raise ValidationError("Only dispatchers and admins can assign riders.")
    if shipment.status in TERMINAL_STATUSES:
        raise ValidationError("Cannot assign a terminal shipment.")
    shipment.rider = rider
    shipment.dispatcher = dispatcher
    shipment.status = Shipment.Status.ASSIGNED
    shipment.save(update_fields=["rider", "dispatcher", "status", "updated_at"])
    create_status_event(shipment, Shipment.Status.ASSIGNED, dispatcher, notes or f"Assigned to {rider.user.get_full_name() or rider.user.email}.")
    return shipment


def reassign_rider(*, shipment: Shipment, rider: RiderProfile, dispatcher: User, notes: str = "") -> Shipment:
    return assign_rider(shipment=shipment, rider=rider, dispatcher=dispatcher, notes=notes or "Shipment reassigned.")


@transaction.atomic
def update_shipment_status(*, shipment: Shipment, status: str, actor: User, notes: str = "") -> Shipment:
    if shipment.status in TERMINAL_STATUSES and shipment.status != status:
        raise ValidationError("Terminal shipments cannot transition to another status.")
    shipment.status = status
    if status == Shipment.Status.PICKED_UP and not shipment.picked_up_at:
        shipment.picked_up_at = timezone.now()
    if status == Shipment.Status.DELIVERED and not shipment.delivered_at:
        shipment.delivered_at = timezone.now()
    shipment.save(update_fields=["status", "picked_up_at", "delivered_at", "updated_at"])
    create_status_event(shipment, status, actor, notes)
    return shipment


def cancel_shipment(*, shipment: Shipment, actor: User, notes: str = "") -> Shipment:
    if actor.role not in {"admin", "dispatcher"} and shipment.customer_id != actor.id:
        raise ValidationError("You cannot cancel this shipment.")
    if shipment.status not in {Shipment.Status.PENDING, Shipment.Status.ASSIGNED}:
        raise ValidationError("Only pending or assigned shipments can be cancelled.")
    return update_shipment_status(shipment=shipment, status=Shipment.Status.CANCELLED, actor=actor, notes=notes or "Shipment cancelled.")


def accept_delivery(*, shipment: Shipment, rider_user: User) -> Shipment:
    if not shipment.rider or shipment.rider.user_id != rider_user.id:
        raise ValidationError("This shipment is not assigned to you.")
    if shipment.status != Shipment.Status.ASSIGNED:
        raise ValidationError("Only assigned shipments can be accepted.")
    return update_shipment_status(shipment=shipment, status=Shipment.Status.ACCEPTED, actor=rider_user, notes="Rider accepted delivery.")


def reject_delivery(*, shipment: Shipment, rider_user: User, notes: str = "") -> Shipment:
    if not shipment.rider or shipment.rider.user_id != rider_user.id:
        raise ValidationError("This shipment is not assigned to you.")
    if shipment.status != Shipment.Status.ASSIGNED:
        raise ValidationError("Only assigned shipments can be rejected.")
    shipment.rider = None
    shipment.status = Shipment.Status.PENDING
    shipment.save(update_fields=["rider", "status", "updated_at"])
    create_status_event(shipment, Shipment.Status.PENDING, rider_user, notes or "Rider rejected delivery.")
    return shipment


@transaction.atomic
def record_delivery_proof(*, shipment: Shipment, actor: User, otp: str, proof_data: dict) -> DeliveryProof:
    if not shipment.rider or shipment.rider.user_id != actor.id:
        raise ValidationError("Only the assigned rider can submit delivery proof.")
    if not verify_delivery_otp(shipment, otp):
        raise ValidationError("Invalid or expired delivery OTP.")
    update_shipment_status(shipment=shipment, status=Shipment.Status.DELIVERED, actor=actor, notes="Delivery proof submitted.")
    proof, _ = DeliveryProof.objects.update_or_create(
        shipment=shipment,
        defaults={
            **proof_data,
            "verified_by": actor,
            "otp_verified": True,
            "receiver_name": proof_data.get("receiver_name") or shipment.recipient_name,
            "receiver_phone": proof_data.get("receiver_phone") or shipment.recipient_phone,
            "signed_at": timezone.now() if proof_data.get("signature") else None,
            "delivered_at": timezone.now(),
        },
    )
    return proof
