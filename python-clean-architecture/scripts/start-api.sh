#!/usr/bin/env sh
set -e

MODE="${1:-dev}"

echo "[startup] current directory: $(pwd)"
echo "[startup] mode=${MODE}"
echo "[startup] applying migrations..."

until alembic upgrade head; do
  echo "[startup] database not ready yet, retrying in 2s..."
  sleep 2
done

echo "[startup] migrations applied"

echo "[startup] running admin seed..."
python scripts/seed_admin.py
echo "[startup] admin seed done"

if [ "$MODE" = "prod" ]; then
  exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --workers 2
fi

exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload