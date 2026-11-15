from __future__ import annotations

import io
import shutil
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from app.services.plates import normalize_plate
from app.services.yolo_detect import yolo_plate_crops

try:
    import pytesseract

    _HAS_TESS = bool(shutil.which("tesseract"))
except ImportError:
    pytesseract = None  # type: ignore
    _HAS_TESS = False


@dataclass
class LprResult:
    plate_number: str
    raw_text: str
    confidence: float


def _decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img


def _preprocess(gray: np.ndarray) -> np.ndarray:
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(gray, 30, 200)
    return edged


def _find_plate_candidates(img: np.ndarray) -> list[np.ndarray]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edged = _preprocess(gray)
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
    h, w = gray.shape[:2]
    crops: list[np.ndarray] = []
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        if len(approx) != 4:
            continue
        x, y, cw, ch = cv2.boundingRect(approx)
        aspect = cw / float(ch) if ch else 0
        area_ratio = (cw * ch) / float(w * h)
        if 2.0 <= aspect <= 6.5 and 0.002 <= area_ratio <= 0.25:
            crop = gray[y : y + ch, x : x + cw]
            if crop.size:
                crops.append(crop)
    if not crops:
        crops.append(gray)
    return crops


def _ocr_crop(crop: np.ndarray) -> tuple[str, float]:
    if not _HAS_TESS or pytesseract is None:
        return "", 0.0
    crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    config = r"--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    data = pytesseract.image_to_data(thresh, config=config, output_type=pytesseract.Output.DICT)
    texts = []
    confidences: list[float] = []
    for text, conf in zip(data["text"], data["conf"], strict=False):
        t = (text or "").strip()
        if not t:
            continue
        try:
            c = float(conf)
        except ValueError:
            continue
        if c >= 0:
            texts.append(t)
            confidences.append(c)
    raw = "".join(texts)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return raw, avg_conf / 100.0


def _all_plate_candidates(img: np.ndarray) -> list[np.ndarray]:
    yolo_crops = yolo_plate_crops(img)
    if yolo_crops:
        return yolo_crops
    return _find_plate_candidates(img)


def recognize_from_bytes(data: bytes) -> LprResult:
    img = _decode_image(data)
    best_raw = ""
    best_conf = 0.0
    best_plate = ""

    for crop in _all_plate_candidates(img):
        raw, conf = _ocr_crop(crop)
        plate = normalize_plate(raw)
        if len(plate) >= 4 and conf >= best_conf:
            best_raw, best_conf, best_plate = raw, conf, plate

    if not best_plate:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        raw, conf = _ocr_crop(gray)
        best_raw, best_conf = raw, conf
        best_plate = normalize_plate(raw)

    if not best_plate:
        raise ValueError(
            "No plate text detected. Install Tesseract OCR (sudo apt install tesseract-ocr) "
            "or enter the plate manually."
        )

    return LprResult(plate_number=best_plate, raw_text=best_raw, confidence=best_conf)


def recognize_from_pil(image: Image.Image) -> LprResult:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return recognize_from_bytes(buf.getvalue())
