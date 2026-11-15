from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth import hash_password
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Alert, User, UserRole
from app.routers import alerts, auth, logs, reports, scan, users, vehicles
from app.services import access as access_service


def migrate_sqlite_alert_types():
    """Rebuild alerts table if an old CHECK constraint blocks AlertType.authorized."""
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='alerts'")
        ).fetchone()
        if not row or not row[0]:
            return
        ddl = row[0]
        if "authorized" in ddl or "CHECK" not in ddl.upper():
            return
        conn.execute(text("ALTER TABLE alerts RENAME TO alerts_legacy_migrate"))
        Alert.__table__.create(bind=conn)
        conn.execute(
            text(
                """
                INSERT INTO alerts (id, alert_type, plate_number, message, is_read, created_at)
                SELECT id, alert_type, plate_number, message, is_read, created_at
                FROM alerts_legacy_migrate
                """
            )
        )
        conn.execute(text("DROP TABLE alerts_legacy_migrate"))


def seed_admin():
    db = SessionLocal()
    try:
        legacy = db.query(User).filter(User.email == "admin@numberplates.local").first()
        if legacy:
            legacy.email = "admin@example.com"
            db.commit()
        if not db.query(User).filter(User.email == "admin@example.com").first():
            db.add(
                User(
                    email="admin@example.com",
                    full_name="System Administrator",
                    hashed_password=hash_password("admin123"),
                    role=UserRole.admin,
                )
            )
            db.commit()
        access_service.check_expiring_vehicles(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_alert_types()
    seed_admin()
    yield


app = FastAPI(
    title="License Plate Recognition Management System",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(scan.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/api/health")
def health():
    db = settings.database_url.split(":", 1)[0]
    return {
        "status": "ok",
        "database": db,
        "yolo_configured": bool(settings.yolo_model_path),
        "smtp_enabled": settings.smtp_enabled,
        "sms_enabled": settings.sms_enabled,
    }
