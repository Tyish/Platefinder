from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import AccessDirection, AccessLog, Alert, AlertType, Vehicle, VehicleStatus
from app.services.notifications import notify_alert
from app.services.plates import normalize_plate

DEDUPE_WINDOW_SECONDS = 60


@dataclass
class AccessResult:
    log: AccessLog
    vehicle: Vehicle | None
    authorized: bool
    alert_created: bool
    deduped: bool


def find_vehicle(db: Session, plate_number: str) -> Vehicle | None:
    normalized = normalize_plate(plate_number)
    return db.query(Vehicle).filter(Vehicle.plate_number == normalized).first()


def record_access(
    db: Session,
    *,
    plate_number: str,
    direction: AccessDirection,
    confidence: float | None,
    recorded_by_id: int | None,
    notes: str | None = None,
    source: str | None = None,
) -> AccessResult:
    normalized = normalize_plate(plate_number)
    vehicle = find_vehicle(db, normalized)
    authorized = False
    new_alerts: list[Alert] = []

    if vehicle and vehicle.status == VehicleStatus.active:
        if vehicle.expiry_date and vehicle.expiry_date.replace(tzinfo=UTC) < datetime.now(UTC):
            vehicle.status = VehicleStatus.expired
            new_alerts.append(
                Alert(
                    alert_type=AlertType.expired,
                    plate_number=normalized,
                    message=f"Vehicle {normalized} license expired on {vehicle.expiry_date.date()}.",
                )
            )
        else:
            authorized = True

    cutoff = datetime.now(UTC) - timedelta(seconds=DEDUPE_WINDOW_SECONDS)
    recent = (
        db.query(AccessLog)
        .filter(AccessLog.plate_number == normalized)
        .order_by(AccessLog.created_at.desc())
        .first()
    )
    if recent is not None and recent.authorized == authorized:
        created = recent.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        if created >= cutoff:
            return AccessResult(
                log=recent,
                vehicle=vehicle,
                authorized=authorized,
                alert_created=False,
                deduped=True,
            )

    note_parts = [p for p in (notes, f"source:{source}" if source else None) if p]
    combined_notes = " | ".join(note_parts) if note_parts else None

    log = AccessLog(
        plate_number=normalized,
        direction=direction,
        authorized=authorized,
        confidence=f"{confidence:.2f}" if confidence is not None else None,
        vehicle_id=vehicle.id if vehicle else None,
        recorded_by_id=recorded_by_id,
        notes=combined_notes,
    )
    db.add(log)

    if authorized:
        owner = vehicle.owner_name if vehicle else "unknown"
        new_alerts.append(
            Alert(
                alert_type=AlertType.authorized,
                plate_number=normalized,
                message=f"Authorized {direction.value}: plate {normalized} ({owner}).",
            )
        )
    else:
        new_alerts.append(
            Alert(
                alert_type=AlertType.unauthorized,
                plate_number=normalized,
                message=f"Unauthorized {direction.value}: plate {normalized} not registered or not active.",
            )
        )

    for alert in new_alerts:
        db.add(alert)

    db.commit()
    db.refresh(log)
    for alert in new_alerts:
        db.refresh(alert)
        notify_alert(alert)

    return AccessResult(
        log=log,
        vehicle=vehicle,
        authorized=authorized,
        alert_created=bool(new_alerts),
        deduped=False,
    )


def check_expiring_vehicles(db: Session, days_ahead: int = 14) -> list[Alert]:
    now = datetime.now(UTC)
    deadline = now + timedelta(days=days_ahead)
    created: list[Alert] = []
    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.status == VehicleStatus.active, Vehicle.expiry_date.isnot(None))
        .all()
    )
    for v in vehicles:
        exp = v.expiry_date
        if exp is None:
            continue
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if now <= exp <= deadline:
            msg = f"Plate {v.plate_number} expires on {exp.date()}."
            exists = (
                db.query(Alert)
                .filter(
                    Alert.plate_number == v.plate_number,
                    Alert.alert_type == AlertType.expiry_soon,
                    Alert.message == msg,
                )
                .first()
            )
            if not exists:
                alert = Alert(alert_type=AlertType.expiry_soon, plate_number=v.plate_number, message=msg)
                db.add(alert)
                created.append(alert)
    if created:
        db.commit()
        for a in created:
            db.refresh(a)
            notify_alert(a)
    return created
