# HTTPS / IP 自签证书说明核对与配置指南

> 适用：无公网域名、仅内网 IP 访问的 FlashApp PWA。

## 1. 对你列出结论的核对

| 结论 | 是否正确 | 说明 |
|------|----------|------|
| HTTPS 页直连 HTTP API 会被混合内容拦截 | **正确** | 浏览器禁止 *active* mixed content（`fetch`/XHR/`ws`） |
| 麦克风 `getUserMedia` 需要安全上下文 | **正确** | HTTPS、或 `localhost`/`127.0.0.1` |
| 摄像头预览 `getUserMedia` 需要安全上下文 | **正确** | 同麦克风 |
| `<input type="file" capture>` 也一定不可用 | **不完全正确** | 多数手机仍可打开系统相机/相册选图；**页内实时预览摄像头**才强制安全上下文。本项目创建页当前用的是 file/capture，录音才走 `getUserMedia` |
| Service Worker / 可安装 PWA 需要 HTTPS | **正确** | 例外：`localhost` |
| 把前端也降成 HTTP 可解决混合内容 | **能通 API，但 PWA/麦克风仍挂** | 除非只用 localhost 调试 |

### 额外关键点（你原文未写全）

1. **`ws://` FunASR 也会被 HTTPS 页拦截**（与 `http://` API 同属混合内容）。必须用 **`wss://` 同源代理**。
2. **自签证书必须装到手机并信任**，否则即使用户点“继续访问”，iOS/Android 上 `getUserMedia` / Service Worker 仍常不可用。
3. **推荐同源架构**：浏览器只访问 `https://<IP>`，`/api` 由网关反代到本机后端；不要让浏览器直连 `http://<IP>:8000`。

```
手机浏览器
  └─ https://10.x.x.x/          (Caddy/Vite，TLS 终止)
        ├─ /                    → frontend/dist
        ├─ /api/*               → 127.0.0.1:8000  (HTTP 本机即可)
        └─ /api/v1/asr/ws       → 后端再连 ws://FunASR
```

## 2. 本仓库已提供的配置

| 文件 | 作用 |
|------|------|
| `scripts/gen-ip-certs.sh` | 为内网 IP 生成自签证书（SAN 含 IP） |
| `certs/` | 证书输出目录（已 gitignore 私钥/证书） |
| `backend/run.sh` | 若存在 `certs/ip.*` 则自动 HTTPS 启动 |
| `backend/src/api/asr.py` | FunASR WebSocket 同源代理 |
| `frontend/vite.config.ts` | 开发/预览启用 HTTPS + `/api` 反代（含 WS） |
| `frontend/run-https.sh` | 一键 HTTPS 前端开发 |
| `Caddyfile` | 生产式单入口：`https://IP` 托管前端并反代 API |

## 3. 快速开始（开发）

```bash
# 1. 生成证书（换成你的内网 IP）
./scripts/gen-ip-certs.sh 10.8.1.23

# 2. 把 certs/ip.crt 安装到手机并「信任」

# 3. 后端（本机 HTTP 即可；或自动 HTTPS）
cd backend && ./run.sh

# 4. 前端 HTTPS（与证书共用）
cd frontend
# 若后端是 HTTP:
export VITE_API_PROXY_TARGET=http://127.0.0.1:8000
./run-https.sh
```

手机访问：`https://10.8.1.23:5173`  
API 走同源 `/api/...`；语音走 `wss://10.8.1.23:5173/api/v1/asr/ws`。

## 4. 快速开始（单入口生产态）

```bash
./scripts/gen-ip-certs.sh 10.8.1.23
# 编辑 Caddyfile，把 10.8.1.23 换成真实 IP

cd frontend && npm run build
cd backend && ./run.sh   # 监听 127.0.0.1:8000 HTTP 即可

# 安装 caddy 后
caddy run --config Caddyfile --adapter caddyfile
```

手机只打开：`https://10.8.1.23`

## 5. 环境变量

### backend `.env`
```bash
HOST=0.0.0.0
PORT=8000
# 可选显式指定（否则自动发现 ../certs/ip.*）
# SSL_CERTFILE=/path/to/ip.crt
# SSL_KEYFILE=/path/to/ip.key
FUNASR_WS_URL=ws://10.17.150.235:10095
```

### frontend `.env`
```bash
# 留空 = 使用同源 /api/v1/asr/ws 代理（推荐）
# VITE_FUNASR_WS_URL=
VITE_HTTPS=true
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
```

## 6. 验收清单

- [ ] 手机已安装并信任 `ip.crt`
- [ ] 地址栏为 `https://<IP>...` 且无持续证书红标
- [ ] 登录接口 `/api/v1/auth/login` 成功
- [ ] 麦克风权限弹窗可出现
- [ ] 语音转写走 `wss://.../api/v1/asr/ws`（DevTools 可见）
- [ ] （可选）PWA「添加到主屏幕」可用
