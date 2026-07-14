#!/usr/bin/env bash
# 开发：Vite HTTPS（与后端共用 certs/ip.*）
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export VITE_HTTPS="${VITE_HTTPS:-true}"
export VITE_DEV_HOST="${VITE_DEV_HOST:-0.0.0.0}"
export VITE_DEV_PORT="${VITE_DEV_PORT:-5173}"

# 后端目标：若后端也开了 HTTPS，设 VITE_API_PROXY_TARGET=https://127.0.0.1:8000
export VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://127.0.0.1:8000}"

if [[ ! -f "$ROOT_DIR/../certs/ip.crt" || ! -f "$ROOT_DIR/../certs/ip.key" ]]; then
  echo "缺少 ../certs/ip.crt / ip.key，请先运行:" >&2
  echo "  ./scripts/gen-ip-certs.sh <你的内网IP>" >&2
  exit 1
fi

exec npm run dev
