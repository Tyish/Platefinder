from __future__ import annotations

import cv2


def capture_jpeg_bytes(rtsp_url: str) -> bytes:
    url = rtsp_url.strip()
    if not url.lower().startswith(("rtsp://", "rtsps://", "http://", "https://")):
        raise ValueError("URL must be rtsp://, rtsps://, http://, or https://")

    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        raise ValueError("Could not open camera stream. Check URL and network.")

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    try:
        # Discard buffered frames so we get a recent image.
        for _ in range(3):
            cap.grab()
        ok, frame = cap.read()
        if not ok or frame is None:
            raise ValueError("No frame received from stream.")
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise ValueError("Failed to encode frame from stream.")
        return encoded.tobytes()
    finally:
        cap.release()
