from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Alert, User
from app.schemas import AlertOut
from app.services import access as access_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Alert)
    if unread_only:
        q = q.filter(Alert.is_read.is_(False))
    return q.order_by(Alert.created_at.desc()).limit(200).all()


@router.post("/check-expiry", response_model=list[AlertOut])
def run_expiry_check(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return access_service.check_expiring_vehicles(db)


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
