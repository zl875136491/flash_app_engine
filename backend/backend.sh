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
  run       启动开发服务器（等同 run.sh）
  health    请求本地健康检查接口
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
  health)
    curl -sS "http://127.0.0.1:${PORT:-8000}/health" | python3 -m json.tool
    ;;
  *)
    usage
    exit 1
    ;;
esac
