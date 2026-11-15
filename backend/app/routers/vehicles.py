from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Vehicle
from app.schemas import VehicleCreate, VehicleOut, VehicleUpdate
from app.services.plates import normalize_plate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
def list_vehicles(
    q: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Vehicle)
    if q:
        needle = f"%{normalize_plate(q)}%"
        query = query.filter(Vehicle.plate_number.like(needle))
    return query.order_by(Vehicle.plate_number).all()


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    body: VehicleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plate = normalize_plate(body.plate_number)
    if db.query(Vehicle).filter(Vehicle.plate_number == plate).first():
        raise HTTPException(status_code=400, detail="Plate already registered")
    vehicle = Vehicle(
        plate_number=plate,
        owner_name=body.owner_name,
        owner_phone=body.owner_phone,
        make_model=body.make_model,
        expiry_date=body.expiry_date,
        registered_by_id=user.id,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: int,
    body: VehicleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete vehicles")
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.commit()
