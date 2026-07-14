#!/usr/bin/env bash
# 后端常用操作入口
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<EOF
用法: ./backend.sh <command>

命令:
  install   安装 Python 依赖
  run       启动开发服务器（等同 run.sh，自动 HTTPS 若有证书）
  worker    启动 Celery Worker（等同 worker.sh）
  health    请求本地健康检查接口
  certs     提示如何生成 IP 证书
EOF
}

cmd="${1:-}"
case "$cmd" in
  install)
    python3 -m pip install -r requirements.txt
    ;;
  run)
    exec ./run.sh
    ;;
  worker)
    exec ./worker.sh
    ;;
  health)
    if [[ -f "$ROOT_DIR/../certs/ip.crt" ]]; then
      curl -skS "https://127.0.0.1:${PORT:-8000}/health" | python3 -m json.tool
    else
      curl -sS "http://127.0.0.1:${PORT:-8000}/health" | python3 -m json.tool
    fi
    ;;
  certs)
    echo "请在仓库根目录执行: ./scripts/gen-ip-certs.sh <内网IP>"
    echo "文档: docs/https_ip_setup.md"
    ;;
  *)
    usage
    exit 1
    ;;
esac
