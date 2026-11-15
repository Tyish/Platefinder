# AI License Plate Recognition Management System

Diploma project implementation: vehicle registration, AI/OCR plate recognition, entry/exit logs, unauthorized alerts, license expiry tracking, RTSP cameras, optional YOLO detection, PDF reports, and email/SMS notifications.

## Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite or **PostgreSQL**
- **Vision:** OpenCV + Tesseract OCR, optional **YOLO** (Ultralytics)
- **Frontend:** React (Vite)
- **Reports:** ReportLab PDF
- **Notifications:** SMTP email, Twilio SMS (optional)

## Prerequisites

- Python 3.11+
- Node.js 20+
- Tesseract OCR (for image recognition): `sudo apt install tesseract-ocr`
- For PostgreSQL: Docker or local Postgres 16+
- For backups (Postgres): `pg_dump` client tools

## Run locally

Use two terminals:

```bash
./scripts/dev-backend.sh
./scripts/dev-frontend.sh
```

Open http://127.0.0.1:5173 — default admin: `admin@example.com` / `admin123`

API docs: http://127.0.0.1:8000/docs

## PostgreSQL

Start Postgres:

```bash
docker compose up -d db
```

Copy env template and point the API at Postgres:

```bash
cp .env.example backend/.env
# DATABASE_URL=postgresql+psycopg2://numberplates:numberplates@127.0.0.1:5432/numberplates
```

Restart the backend. Tables are created automatically on startup.

### Backups

```bash
./scripts/backup-db.sh
```

Writes timestamped backups under `backups/` (SQLite copy or Postgres `pg_dump`).

## Optional: YOLO plate detection

Install extra dependencies and set a trained `.pt` model path (e.g. from Roboflow / custom training):

```bash
cd backend && . .venv/bin/activate
pip install -r requirements-yolo.txt
```

In `backend/.env`:

```env
YOLO_MODEL_PATH=/path/to/license_plate_detector.pt
YOLO_CONFIDENCE=0.35
```

When configured, YOLO bounding boxes are used before OpenCV contour detection.

## IP camera / RTSP

In the UI: **Scan plate → IP camera / RTSP stream**, or API:

`POST /api/scan/rtsp` with `{ "rtsp_url": "rtsp://...", "direction": "entry" }`

## PDF reports

UI: **Reports** — download access logs or security summary PDF.

API:

- `GET /api/reports/access-logs.pdf`
- `GET /api/reports/security-summary.pdf`

## Email & SMS alerts

Alerts (unauthorized, expiry, expired) trigger optional outbound notifications when enabled in `backend/.env` (see `.env.example`):

- **SMTP** — `SMTP_ENABLED=true`, host, credentials, `NOTIFY_EMAIL_TO`
- **SMS (Twilio)** — `SMS_ENABLED=true`, Twilio SID/token/from, `NOTIFY_SMS_TO`

In-app alerts are always stored regardless of SMTP/SMS settings.

## Demo flow

1. Register vehicles on **Vehicles**
2. **Scan plate** — manual, image upload, or RTSP URL
3. Review **Access logs** and **Alerts**
4. **Reports** — PDF for security officers
5. **Alerts → Run expiry check** for licenses expiring within 14 days

## Project layout

```
backend/app/          API, models, LPR, RTSP, reports, notifications
frontend/src/         Admin UI
docker-compose.yml    PostgreSQL for production-style dev
scripts/              dev servers, database backup, verification
```

## Proposal alignment (complete)

| Proposal requirement | Implementation |
|---------------------|----------------|
| Register authorized vehicles | `Vehicles` module + API |
| Automatic plate recognition | OpenCV + Tesseract; optional YOLO |
| Entry / exit monitoring | Access logs + scan (manual, image, RTSP) |
| Unauthorized detection | Alerts + access log flag |
| Renewal / expiry tracking | Vehicle `expiry_date`, expiry check job |
| Notifications | In-app alerts + optional email/SMS |
| Reports for security staff | PDF exports (access + security summary) |
| Database | SQLite (dev) or PostgreSQL + backup script |
| User roles | Admin, security, parking, traffic (API + seed admin) |

Verify everything before a demo or submission:

```bash
./scripts/verify-system.sh      # quick smoke test
./scripts/test-all.sh           # full API + frontend build tests
```

Default admin after first start: `admin@example.com` / `admin123` (legacy `admin@numberplates.local` is migrated automatically).
