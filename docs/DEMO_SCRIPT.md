# Final presentation demo script (5–8 minutes)

1. **Introduction** — Show login and dashboard (registered vehicles, unread alerts).
2. **Vehicle registration** — Add a plate (e.g. `KAA123A`) with owner and expiry date.
3. **Authorized access** — Scan plate → Manual entry with the same plate → show authorized badge and log row.
4. **Unauthorized access** — Scan unknown plate → show alert and access log.
5. **Expiry** — Set a vehicle expiry within 14 days → Alerts → Run expiry check → show new alert.
6. **Reports** — Download security summary PDF for officers.
7. **Optional** — Image upload or RTSP URL if camera/Tesseract is available; mention YOLO when `YOLO_MODEL_PATH` is configured.

**Credentials:** `admin@example.com` / `admin123` (change in production).

**Backup line:** System uses AI-based LPR with a management layer matching the project proposal: registration, monitoring, alerts, and reporting.
