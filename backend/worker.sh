#!/usr/bin/env bash
# 启动 Celery Worker
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export PYTHONPATH="${ROOT_DIR}${PYTHONPATH:+:$PYTHONPATH}"

exec celery -A src.core.celery_app.celery_app worker \
  --loglevel="${CELERY_LOGLEVEL:-INFO}" \
  --concurrency="${CELERY_CONCURRENCY:-1}" \
  -Q flashapp
