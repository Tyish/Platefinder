from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import AccessLogOut, ManualScanRequest, RtspScanRequest, ScanResult, VehicleOut
from app.services import access as access_service
from app.services import lpr, rtsp

router = APIRouter(prefix="/scan", tags=["scan"])


def _to_scan_result(
    result: access_service.AccessResult,
    plate: str,
    raw: str,
    conf: float,
) -> ScanResult:
    return ScanResult(
        plate_number=plate,
        raw_text=raw,
        confidence=conf,
        authorized=result.authorized,
        vehicle=VehicleOut.model_validate(result.vehicle) if result.vehicle else None,
        access_log=AccessLogOut.model_validate(result.log),
        detected=True,
        alert_created=result.alert_created,
        deduped=result.deduped,
    )


def _empty_scan_result(raw: str = "", conf: float = 0.0) -> ScanResult:
    return ScanResult(
        plate_number=None,
        raw_text=raw,
        confidence=conf,
        authorized=False,
        vehicle=None,
        access_log=None,
        detected=False,
        alert_created=False,
        deduped=False,
    )


@router.post("/image", response_model=ScanResult)
async def scan_image(
    direction: str = "entry",
    source: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models import AccessDirection

    try:
        dir_enum = AccessDirection(direction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="direction must be entry or exit") from e

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        ocr = lpr.recognize_from_bytes(data)
    except ValueError:
        return _empty_scan_result()

    if not ocr.plate_number or len(ocr.plate_number) < 4:
        return _empty_scan_result(ocr.raw_text, ocr.confidence)

    result = access_service.record_access(
        db,
        plate_number=ocr.plate_number,
        direction=dir_enum,
        confidence=ocr.confidence,
        recorded_by_id=user.id,
        source=source,
    )
    return _to_scan_result(result, ocr.plate_number, ocr.raw_text, ocr.confidence)


@router.post("/manual", response_model=ScanResult)
def scan_manual(
    body: ManualScanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = access_service.record_access(
        db,
        plate_number=body.plate_number,
        direction=body.direction,
        confidence=1.0,
        recorded_by_id=user.id,
        notes="Manual entry",
    )
    plate = result.log.plate_number
    return _to_scan_result(result, plate, plate, 1.0)


@router.post("/rtsp", response_model=ScanResult)
def scan_rtsp(
    body: RtspScanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        frame = rtsp.capture_jpeg_bytes(body.rtsp_url)
        ocr = lpr.recognize_from_bytes(frame)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if not ocr.plate_number or len(ocr.plate_number) < 4:
        return _empty_scan_result(ocr.raw_text, ocr.confidence)

    result = access_service.record_access(
        db,
        plate_number=ocr.plate_number,
        direction=body.direction,
        confidence=ocr.confidence,
        recorded_by_id=user.id,
        notes=f"RTSP: {body.rtsp_url[:120]}",
    )
    return _to_scan_result(result, ocr.plate_number, ocr.raw_text, ocr.confidence)
