from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import AccessLog, User
from app.schemas import AccessLogOut

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[AccessLogOut])
def list_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(AccessLog).order_by(AccessLog.created_at.desc()).limit(min(limit, 500)).all()
