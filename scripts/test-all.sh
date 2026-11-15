#!/usr/bin/env bash
# Full feature test suite — run with backend on :8000
set -uo pipefail
BASE="${API_BASE:-http://127.0.0.1:8000}"
PASS=0
FAIL=0
SKIP=0

pass() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }
skip() { echo "  ○ SKIP: $1"; SKIP=$((SKIP + 1)); }

need_json() {
  python3 -c 'import sys,json; json.load(sys.stdin)' >/dev/null 2>&1
}

echo "=============================================="
echo " LPR Management System — full test run"
echo " API: $BASE"
echo "=============================================="

echo ""
echo "[1] Health & feature flags"
if HEALTH=$(curl -sf "$BASE/api/health" 2>/dev/null) && echo "$HEALTH" | need_json; then
  pass "GET /api/health"
  echo "$HEALTH" | python3 -m json.tool | sed 's/^/      /'
else
  fail "GET /api/health — is the backend running? (./scripts/dev-backend.sh)"
  echo ""
  echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"
  exit 1
fi

echo ""
echo "[2] Authentication"
TOKEN=""
if RESP=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=admin123' 2>/dev/null); then
  TOKEN=$(echo "$RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
  pass "POST /api/auth/login (admin)"
else
  fail "POST /api/auth/login"
fi

if [[ -z "$TOKEN" ]]; then
  echo "Cannot continue without token."
  exit 1
fi
AUTH="Authorization: Bearer $TOKEN"

if curl -sf -H "$AUTH" "$BASE/api/auth/me" | need_json; then
  pass "GET /api/auth/me"
else
  fail "GET /api/auth/me"
fi

BAD_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=wrong')
if [[ "$BAD_CODE" == "401" ]]; then
  pass "Login rejects bad password (401)"
else
  fail "Login should return 401 for bad password"
fi

echo ""
echo "[3] Vehicles"
PLATE="TEST$(date +%s | tail -c 6)X"
if curl -sf -X POST "$BASE/api/vehicles" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"plate_number\":\"$PLATE\",\"owner_name\":\"Test Owner\",\"make_model\":\"Demo\"}" | need_json; then
  pass "POST /api/vehicles (register $PLATE)"
else
  fail "POST /api/vehicles"
fi

if curl -sf -H "$AUTH" "$BASE/api/vehicles?q=$PLATE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert any(v['plate_number']==('$PLATE'.upper().replace(' ','')) or v['plate_number']=='$PLATE' for v in d)" 2>/dev/null; then
  pass "GET /api/vehicles?search"
else
  # normalize might strip - try contains
  if curl -sf -H "$AUTH" "$BASE/api/vehicles" | grep -q "$PLATE"; then
    pass "GET /api/vehicles (list contains new plate)"
  else
    fail "GET /api/vehicles search/list"
  fi
fi

echo ""
echo "[4] Scan — manual (authorized + unauthorized)"
if curl -sf -X POST "$BASE/api/scan/manual" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"plate_number\":\"$PLATE\",\"direction\":\"entry\"}" | python3 -c \
  'import sys,json; d=json.load(sys.stdin); assert d["authorized"] is True' 2>/dev/null; then
  pass "POST /api/scan/manual — authorized vehicle"
else
  fail "POST /api/scan/manual — authorized"
fi

UNK="UNK$(date +%s | tail -c 7)"
if curl -sf -X POST "$BASE/api/scan/manual" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"plate_number\":\"$UNK\",\"direction\":\"exit\"}" | python3 -c \
  'import sys,json; d=json.load(sys.stdin); assert d["authorized"] is False' 2>/dev/null; then
  pass "POST /api/scan/manual — unauthorized plate"
else
  fail "POST /api/scan/manual — unauthorized"
fi

echo ""
echo "[5] Access logs"
if curl -sf -H "$AUTH" "$BASE/api/logs" | python3 -c "import sys,json; assert len(json.load(sys.stdin))>=2" 2>/dev/null; then
  pass "GET /api/logs (has entries)"
else
  fail "GET /api/logs"
fi

echo ""
echo "[6] Alerts & expiry check"
if curl -sf -H "$AUTH" "$BASE/api/alerts" | need_json; then
  pass "GET /api/alerts"
else
  fail "GET /api/alerts"
fi

if curl -sf -X POST -H "$AUTH" "$BASE/api/alerts/check-expiry" | need_json; then
  pass "POST /api/alerts/check-expiry"
else
  fail "POST /api/alerts/check-expiry"
fi

echo ""
echo "[7] PDF reports"
for path in access-logs security-summary; do
  HDR=$(curl -sf -H "$AUTH" "$BASE/api/reports/${path}.pdf" | head -c 4)
  if [[ "$HDR" == "%PDF" ]]; then
    pass "GET /api/reports/${path}.pdf"
  else
    fail "GET /api/reports/${path}.pdf (not PDF)"
  fi
done

echo ""
echo "[8] RTSP / IP camera scan"
CODE=$(curl -s -o /tmp/rtsp-test.json -w "%{http_code}" -X POST "$BASE/api/scan/rtsp" \
  -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"rtsp_url":"rtsp://127.0.0.1:1/invalid","direction":"entry"}')
if [[ "$CODE" == "422" ]]; then
  pass "POST /api/scan/rtsp — invalid stream returns 422"
else
  fail "POST /api/scan/rtsp — expected 422 for bad URL, got $CODE"
fi

echo ""
echo "[9] Image upload + OCR"
if command -v tesseract >/dev/null 2>&1; then
  IMG=$(mktemp --suffix=.png)
  python3 <<PY
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB", (320, 80), "white")
d = ImageDraw.Draw(img)
d.text((20, 20), "KAA123A", fill="black")
img.save("$IMG")
PY
  if curl -sf -X POST -H "$AUTH" \
    -F "file=@$IMG;type=image/png" \
    "$BASE/api/scan/image?direction=entry" | need_json; then
    pass "POST /api/scan/image (Tesseract available)"
  else
    fail "POST /api/scan/image"
  fi
  rm -f "$IMG"
else
  skip "POST /api/scan/image — install tesseract-ocr for OCR tests"
fi

echo ""
echo "[10] Users (admin)"
if curl -sf -H "$AUTH" "$BASE/api/users" | need_json; then
  pass "GET /api/users (admin)"
else
  fail "GET /api/users"
fi

echo ""
echo "[11] PostgreSQL (optional)"
if docker compose -f "$(dirname "$0")/../docker-compose.yml" ps --status running 2>/dev/null | grep -q numberplates-db; then
  if PGPASS=$(grep DATABASE_URL "$(dirname "$0")/../backend/.env" 2>/dev/null | grep -q postgresql && echo yes); then
    pass "Postgres container running (ensure DATABASE_URL in backend/.env)"
  else
    skip "Postgres container running but backend may still use SQLite — set backend/.env DATABASE_URL"
  fi
else
  skip "PostgreSQL — run: docker compose up -d db && configure backend/.env"
fi

echo ""
echo "[12] YOLO (optional)"
if echo "$HEALTH" | python3 -c 'import sys,json; import sys; d=json.load(sys.stdin); exit(0 if d.get("yolo_configured") else 1)' 2>/dev/null; then
  pass "YOLO model path configured in environment"
else
  skip "YOLO — set YOLO_MODEL_PATH + pip install -r requirements-yolo.txt"
fi

echo ""
echo "[13] Email / SMS (optional)"
if echo "$HEALTH" | python3 -c 'import sys,json; d=json.load(sys.stdin); exit(0 if d.get("smtp_enabled") or d.get("sms_enabled") else 1)' 2>/dev/null; then
  pass "SMTP or SMS enabled in environment"
else
  skip "Email/SMS — enable SMTP_ENABLED or SMS_ENABLED in backend/.env to test live delivery"
fi

echo ""
echo "[14] Frontend build"
if (cd "$(dirname "$0")/../frontend" && npm run build >/tmp/np-fe-build.log 2>&1); then
  pass "npm run build (frontend)"
else
  fail "npm run build — see /tmp/np-fe-build.log"
fi

echo ""
echo "=============================================="
echo " SUMMARY: $PASS passed, $FAIL failed, $SKIP skipped"
echo "=============================================="
[[ "$FAIL" -eq 0 ]]
