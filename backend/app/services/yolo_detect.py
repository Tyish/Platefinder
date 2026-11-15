from __future__ import annotations

import logging

import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)
_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    if not settings.yolo_model_path:
        return None
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        logger.warning("YOLO enabled but ultralytics not installed: %s", exc)
        return None
    _model = YOLO(settings.yolo_model_path)
    return _model


def yolo_plate_crops(img_bgr: np.ndarray) -> list[np.ndarray]:
    """Return grayscale plate candidate crops from a YOLO detector, if configured."""
    model = _load_model()
    if model is None:
        return []

    gray_full = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    results = model.predict(img_bgr, conf=settings.yolo_confidence, verbose=False)
    crops: list[np.ndarray] = []
    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes.xyxy.cpu().numpy():
            x1, y1, x2, y2 = [int(v) for v in box]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(gray_full.shape[1], x2), min(gray_full.shape[0], y2)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = gray_full[y1:y2, x1:x2]
            if crop.size:
                crops.append(crop)
    return crops
