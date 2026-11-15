from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.services import reports as report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/access-logs.pdf")
def access_logs_pdf(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pdf = report_service.build_access_logs_pdf(db)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="access-logs.pdf"'},
    )


@router.get("/security-summary.pdf")
def security_summary_pdf(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    pdf = report_service.build_security_summary_pdf(db)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="security-summary.pdf"'},
    )
