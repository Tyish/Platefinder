from __future__ import annotations

import io
from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models import AccessLog, Alert, Vehicle


def _fmt_dt(value: datetime | None) -> str:
    if not value:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


def build_access_logs_pdf(db: Session, *, limit: int = 500) -> bytes:
    logs = db.query(AccessLog).order_by(AccessLog.created_at.desc()).limit(limit).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Access Logs Report")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("License Plate Recognition — Access Logs", styles["Title"]),
        Paragraph(f"Generated: {_fmt_dt(datetime.now(UTC))}", styles["Normal"]),
        Spacer(1, 12),
    ]
    data = [["Time", "Plate", "Direction", "Authorized", "Confidence"]]
    for log in logs:
        data.append(
            [
                _fmt_dt(log.created_at),
                log.plate_number,
                log.direction.value,
                "Yes" if log.authorized else "No",
                log.confidence or "—",
            ]
        )
    table = Table(data, repeatRows=1, colWidths=[120, 70, 60, 70, 60])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


def build_security_summary_pdf(db: Session) -> bytes:
    vehicles = db.query(Vehicle).order_by(Vehicle.plate_number).all()
    unread_alerts = db.query(Alert).filter(Alert.is_read.is_(False)).order_by(Alert.created_at.desc()).limit(100).all()
    recent_denied = (
        db.query(AccessLog)
        .filter(AccessLog.authorized.is_(False))
        .order_by(AccessLog.created_at.desc())
        .limit(50)
        .all()
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title="Security Summary")
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Security Officer Summary Report", styles["Title"]),
        Paragraph(f"Generated: {_fmt_dt(datetime.now(UTC))}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Registered vehicles: {len(vehicles)}", styles["Heading2"]),
        Paragraph(f"Unread alerts: {len(unread_alerts)}", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph("Recent unauthorized access attempts", styles["Heading3"]),
    ]

    denied_data = [["Time", "Plate", "Direction"]]
    for log in recent_denied:
        denied_data.append([_fmt_dt(log.created_at), log.plate_number, log.direction.value])
    if len(denied_data) == 1:
        denied_data.append(["—", "None", "—"])
    denied_table = Table(denied_data, repeatRows=1)
    denied_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    story.extend([denied_table, Spacer(1, 12), Paragraph("Open alerts", styles["Heading3"])])

    alert_data = [["Time", "Type", "Plate", "Message"]]
    for alert in unread_alerts:
        alert_data.append([_fmt_dt(alert.created_at), alert.alert_type.value, alert.plate_number, alert.message[:80]])
    if len(alert_data) == 1:
        alert_data.append(["—", "—", "—", "No unread alerts"])
    alert_table = Table(alert_data, repeatRows=1, colWidths=[95, 70, 60, 250])
    alert_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    story.append(alert_table)
    doc.build(story)
    return buffer.getvalue()
