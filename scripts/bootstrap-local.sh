#!/bin/sh
set -eu

PROFILE="${BRIXTA_LOCAL_PROFILE:-full}"
case "$PROFILE" in
  api|full) ;;
  *) echo "BRIXTA_LOCAL_PROFILE must be 'api' or 'full'." >&2; exit 1 ;;
esac

if [ -n "${PYTHON_BIN:-}" ]; then
  CANDIDATES="$PYTHON_BIN"
else
  CANDIDATES="python3.11 python3.12 python3.13"
fi

PYTHON_BIN=""
for candidate in $CANDIDATES; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo "BRIXTA needs Python 3.11, 3.12, or 3.13. Set PYTHON_BIN if necessary." >&2
  exit 1
fi

VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "$VERSION" in
  3.11|3.12|3.13) ;;
  *) echo "Unsupported Python $VERSION. Use Python 3.11–3.13." >&2; exit 1 ;;
esac

if [ ! -d Resea ]; then
  "$PYTHON_BIN" -m venv Resea
fi

Resea/bin/python -m pip install --upgrade pip
if [ "$PROFILE" = "full" ]; then
  Resea/bin/python -m pip install \
    -r requirements-workers.txt \
    -r requirements-rag.txt \
    -r requirements-plugins.txt
else
  Resea/bin/python -m pip install \
    -r requirements-api.txt \
    -r requirements-rag.txt \
    -r requirements-plugins.txt
fi
Resea/bin/python -m pip install -e .

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example; review its passwords before continuing."
fi

if command -v docker >/dev/null 2>&1; then
  docker compose up -d --wait postgres redis minio
  docker compose run --rm minio-init
else
  echo "Docker was not found; start PostgreSQL/pgvector, Redis, and MinIO yourself."
fi

if command -v npm >/dev/null 2>&1; then
  (cd infra && npm ci && npm run db:migrate)
  (cd brixta-dashboard && npm ci)
else
  echo "npm was not found; install Node.js before running migrations or the dashboard."
fi

echo
echo "BRIXTA local setup is ready."
echo "  source Resea/bin/activate"
echo "  brixta doctor"
echo "  python -m uvicorn api.main:app --reload"
echo "  python -m celery -A runtime.celery_app.celery worker --loglevel=info"
echo "  python -m celery -A runtime.celery_app.celery beat --loglevel=info"
echo "  (cd brixta-dashboard && npm run dev)"
