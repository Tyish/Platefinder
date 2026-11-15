from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import AccessDirection, AlertType, UserRole, VehicleStatus


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)
    role: UserRole = UserRole.security


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class VehicleCreate(BaseModel):
    plate_number: str
    owner_name: str
    owner_phone: str | None = None
    make_model: str | None = None
    expiry_date: datetime | None = None


class VehicleUpdate(BaseModel):
    owner_name: str | None = None
    owner_phone: str | None = None
    make_model: str | None = None
    expiry_date: datetime | None = None
    status: VehicleStatus | None = None


class VehicleOut(BaseModel):
    id: int
    plate_number: str
    owner_name: str
    owner_phone: str | None
    make_model: str | None
    expiry_date: datetime | None
    status: VehicleStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class AccessLogOut(BaseModel):
    id: int
    plate_number: str
    direction: AccessDirection
    authorized: bool
    confidence: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertOut(BaseModel):
    id: int
    alert_type: AlertType
    plate_number: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanResult(BaseModel):
    plate_number: str | None = None
    raw_text: str = ""
    confidence: float = 0.0
    authorized: bool = False
    vehicle: VehicleOut | None = None
    access_log: AccessLogOut | None = None
    detected: bool = True
    alert_created: bool = False
    deduped: bool = False


class ManualScanRequest(BaseModel):
    plate_number: str
    direction: AccessDirection = AccessDirection.entry


class RtspScanRequest(BaseModel):
    rtsp_url: str = Field(min_length=8)
    direction: AccessDirection = AccessDirection.entry
