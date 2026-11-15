import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    security = "security"
    parking = "parking"
    traffic = "traffic"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.security)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="registered_by")


class VehicleStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    suspended = "suspended"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    owner_name: Mapped[str] = mapped_column(String(255))
    owner_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    make_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[VehicleStatus] = mapped_column(Enum(VehicleStatus), default=VehicleStatus.active)
    registered_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    registered_by: Mapped["User | None"] = relationship(back_populates="vehicles")
    access_logs: Mapped[list["AccessLog"]] = relationship(back_populates="vehicle")


class AccessDirection(str, enum.Enum):
    entry = "entry"
    exit = "exit"


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(32), index=True)
    direction: Mapped[AccessDirection] = mapped_column(Enum(AccessDirection))
    authorized: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    recorded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vehicle: Mapped["Vehicle | None"] = relationship(back_populates="access_logs")


class AlertType(str, enum.Enum):
    unauthorized = "unauthorized"
    authorized = "authorized"
    expiry_soon = "expiry_soon"
    expired = "expired"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, native_enum=False, create_constraint=False, length=32)
    )
    plate_number: Mapped[str] = mapped_column(String(32), index=True)
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
