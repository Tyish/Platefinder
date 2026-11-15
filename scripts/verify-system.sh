#!/usr/bin/env bash
# End-to-end smoke test for demo / submission checklist.
set -euo pipefail
BASE="${API_BASE:-http://127.0.0.1:8000}"

echo "== Health =="
curl -sf "$BASE/api/health" | python3 -m json.tool

echo "== Login =="
TOKEN=$(curl -sf -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=admin123' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
AUTH="Authorization: Bearer $TOKEN"

echo "== Register vehicle =="
curl -sf -X POST "$BASE/api/vehicles" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"plate_number":"DEMO99Z","owner_name":"Demo User"}' >/dev/null

echo "== Manual scan (authorized) =="
curl -sf -X POST "$BASE/api/scan/manual" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"plate_number":"DEMO99Z","direction":"entry"}' | python3 -c \
  'import sys,json; d=json.load(sys.stdin); assert d["authorized"] is True; print("plate", d["plate_number"])'

echo "== PDF reports =="
curl -sf -H "$AUTH" "$BASE/api/reports/access-logs.pdf" | head -c 5 | grep -q '%PDF' && echo "access-logs.pdf OK"
curl -sf -H "$AUTH" "$BASE/api/reports/security-summary.pdf" | head -c 5 | grep -q '%PDF' && echo "security-summary.pdf OK"

echo ""
echo "All checks passed."
