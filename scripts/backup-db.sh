#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [[ -f "$ROOT/backend/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/backend/.env"
fi

URL="${DATABASE_URL:-sqlite:///./numberplates.db}"

if [[ "$URL" == postgresql* ]]; then
  PG_URL="${URL/postgresql+psycopg2:/postgresql:}"
  PG_URL="${PG_URL/postgresql+psycopg:/postgresql:}"
  OUT="$BACKUP_DIR/postgres-$STAMP.sql.gz"
  echo "Backing up PostgreSQL to $OUT"
  pg_dump "$PG_URL" | gzip > "$OUT"
else
  DB_FILE="$ROOT/backend/numberplates.db"
  if [[ ! -f "$DB_FILE" ]]; then
    echo "SQLite database not found at $DB_FILE"
    exit 1
  fi
  OUT="$BACKUP_DIR/sqlite-$STAMP.db"
  cp "$DB_FILE" "$OUT"
  echo "Copied SQLite backup to $OUT"
fi

echo "Done."
