#!/usr/bin/env bash
# 为内网 IP 生成自签 HTTPS 证书（无需域名）
# 用法:
#   ./scripts/gen-ip-certs.sh 10.8.1.23
#   ./scripts/gen-ip-certs.sh 10.8.1.23 192.168.1.10
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${CERT_DIR:-$ROOT_DIR/certs}"
DAYS="${CERT_DAYS:-825}"

if [[ $# -lt 1 ]]; then
  echo "用法: $0 <主IP> [附加IP...]"
  echo "示例: $0 10.8.1.23"
  exit 1
fi

PRIMARY_IP="$1"
shift || true
EXTRA_IPS=("$@")

mkdir -p "$CERT_DIR"
CONF="$CERT_DIR/openssl-ip.cnf"
KEY="$CERT_DIR/ip.key"
CRT="$CERT_DIR/ip.crt"

{
  echo "[req]"
  echo "default_bits = 2048"
  echo "prompt = no"
  echo "default_md = sha256"
  echo "distinguished_name = dn"
  echo "x509_extensions = v3_req"
  echo
  echo "[dn]"
  echo "C = CN"
  echo "O = FlashApp Engine"
  echo "CN = $PRIMARY_IP"
  echo
  echo "[v3_req]"
  echo "basicConstraints = CA:FALSE"
  echo "keyUsage = digitalSignature, keyEncipherment"
  echo "extendedKeyUsage = serverAuth"
  echo "subjectAltName = @alt_names"
  echo
  echo "[alt_names]"
  echo "IP.1 = $PRIMARY_IP"
  echo "IP.2 = 127.0.0.1"
  idx=3
  for ip in "${EXTRA_IPS[@]:-}"; do
    [[ -z "$ip" ]] && continue
    echo "IP.$idx = $ip"
    idx=$((idx + 1))
  done
  echo "DNS.1 = localhost"
} >"$CONF"

openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$KEY" \
  -out "$CRT" \
  -days "$DAYS" \
  -config "$CONF"

chmod 600 "$KEY"
cat >"$CERT_DIR/README.md" <<EOF
# IP HTTPS 证书

- 主 IP: \`$PRIMARY_IP\`
- 证书: \`ip.crt\`
- 私钥: \`ip.key\`
- 有效期: ${DAYS} 天

## 手机 / 浏览器信任（必须）

自签证书默认不被信任。内网无公网 CA 时，请在设备上安装并信任 \`ip.crt\`：

### Android
1. 将 \`ip.crt\` 传到手机
2. 设置 → 安全 → 加密与凭据 → 安装证书 → CA 证书
3. 用 Chrome 打开 \`https://$PRIMARY_IP\`

### iOS
1. AirDrop / 文件传 \`ip.crt\`
2. 设置 → 已下载描述文件 → 安装
3. 设置 → 通用 → 关于本机 → 证书信任设置 → 启用完全信任

### 桌面 Chrome（临时调试）
直接访问时点「高级 → 继续前往」（仅内网自签适用）。

> 注意：部分移动浏览器在未信任 CA 时，即使用户点继续，\`getUserMedia\` / Service Worker 仍可能不可用。
> **请优先安装并信任证书**，不要只靠“继续访问”。
EOF

echo "已生成:"
echo "  $CRT"
echo "  $KEY"
echo "请将证书安装到手机并信任，详见 $CERT_DIR/README.md"
