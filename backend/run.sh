#!/usr/bin/env bash
# 开发环境启动 FastAPI（支持可选 HTTPS）
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
SSL_CERTFILE="${SSL_CERTFILE:-}"
SSL_KEYFILE="${SSL_KEYFILE:-}"

# 未显式指定时，若仓库 certs/ 存在则自动启用 HTTPS
if [[ -z "$SSL_CERTFILE" && -f "$ROOT_DIR/../certs/ip.crt" ]]; then
  SSL_CERTFILE="$ROOT_DIR/../certs/ip.crt"
fi
if [[ -z "$SSL_KEYFILE" && -f "$ROOT_DIR/../certs/ip.key" ]]; then
  SSL_KEYFILE="$ROOT_DIR/../certs/ip.key"
fi

ARGS=(uvicorn main:app --host "$HOST" --port "$PORT" --reload)

if [[ -n "$SSL_CERTFILE" && -n "$SSL_KEYFILE" ]]; then
  if [[ ! -f "$SSL_CERTFILE" || ! -f "$SSL_KEYFILE" ]]; then
    echo "SSL_CERTFILE/SSL_KEYFILE 指向的文件不存在" >&2
    exit 1
  fi
  ARGS+=(--ssl-certfile "$SSL_CERTFILE" --ssl-keyfile "$SSL_KEYFILE")
  echo "HTTPS 已启用: https://${HOST}:${PORT}"
else
  echo "HTTP 模式: http://${HOST}:${PORT}（未找到证书时）"
fi

exec "${ARGS[@]}"
