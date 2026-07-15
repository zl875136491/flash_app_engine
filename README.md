# FlashApp Engine

面向公司内网的「口述即部署」轻量云计算平台：手机 PWA 输入需求（语音 / 图片），后端 AI 编排自动完成架构解析、代码生成、Docker 沙箱构建与验证，并暴露可分享的内网 Web 应用。

## 功能概览

| 能力 | 说明 |
|------|------|
| ITCode 登录 | 白名单 ITCode 校验后签发 JWT（见 [docs/auth_users.md](docs/auth_users.md)） |
| 语音创建 | FunASR 实时转写；HTTPS 下同源 `wss` 代理，避免混合内容 |
| 图片辅助 | 上传草图 / 截图，参与任务需求 |
| 异步编排 | Celery 消费任务：Analyzing → Coding → Building → Verifying → Success / Failed |
| 沙箱部署 | Docker 构建与端口映射（`30000–40000`）；失败可自愈一次 |
| 应用额度 | 每用户同时 **运行中（Success）** 上限 2；列表展示「运行中 x/2」 |
| 生命周期 | 停止 / 启动 / 移除；失败任务可重试 |
| PWA | 可安装到主屏幕；登录页提供安装引导气泡 |

产品愿景与早期规约见 [docs/prd.md](docs/prd.md)。内网模型与 HTTPS 说明见 [docs/local_models.md](docs/local_models.md)、[docs/https_ip_setup.md](docs/https_ip_setup.md)。

## 仓库结构

```
flash_app_engine/
├── backend/          # FastAPI + Celery Worker
├── frontend/         # React 19 + Vite + PWA
├── certs/            # 内网 IP 自签证书（gitignore）
├── docs/             # 文档、PRD、模型说明、图标源文件
├── Caddyfile         # 可选：Caddy 单入口 HTTPS
└── scripts/          # 证书生成等脚本
```

## 技术栈

- **前端**：React 19、Vite、Tailwind CSS 4、vite-plugin-pwa、移动端优先
- **后端**：Python 3.10+、FastAPI、Beanie/MongoDB、Celery/Redis
- **运行时**：Docker 沙箱、Nginx（或 Caddy）反代

## 本地 / 本机部署（当前环境）

### 依赖服务

- MongoDB（需认证时在 `.env` 配置 `MONGODB_URI`）
- Redis（有密码时使用 `redis://:PASSWORD@127.0.0.1:6379/0`）
- Docker（沙箱构建；不可用时可 `SANDBOX_MOCK=true`）

### 后端

```bash
cd backend
python3 -m venv ../../venv   # 或复用已有 venv
source ../../venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # 按环境修改
./run.sh                     # 或 systemctl: bk.flashapp.8000
./worker.sh                  # 或 systemctl: bk.flashapp.worker
```

主要配置见 `backend/.env.example`：`USER_APP_RUNNING_LIMIT`、模型地址、`FUNASR_WS_URL`、`SANDBOX_PUBLIC_HOST` 等。

### 前端

```bash
cd frontend
npm ci
# 从源图生成 PWA 图标（可选）
# python3 scripts/gen-pwa-icons.py
npm run build                # 产出 dist/
```

开发 HTTPS（需先 `./scripts/gen-ip-certs.sh <内网IP>`）：

```bash
./run-https.sh
```

### HTTPS 与访问

内网无公网域名时，用自签证书 + 信任证书后访问，麦克风与 PWA 才可用：

```bash
./scripts/gen-ip-certs.sh 10.32.12.110
```

当前推荐入口（本机已配置 Nginx）：

- **https://10.32.12.110**（HTTP `:8100` 会 301 到 HTTPS）
- 首次请在手机安装并信任 `certs/ip.crt`（详见 [docs/https_ip_setup.md](docs/https_ip_setup.md)）

systemd 单元示例：`bk.flashapp.8000`（API）、`bk.flashapp.worker`（Celery）。

## 主要 API（需 Bearer JWT，前缀 `/api/v1`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | ITCode 登录 |
| GET | `/auth/me` | 当前用户 |
| GET | `/tasks/quota` | 运行额度 `limit/used/remaining` |
| GET | `/tasks` | 任务列表（含 `quota`） |
| POST | `/tasks` | 创建任务（额度满返回 409） |
| GET | `/tasks/{id}` | 任务详情 |
| POST | `/tasks/{id}/stop` | 停止运行中应用 → `Stopped` |
| POST | `/tasks/{id}/start` | 启动已停止应用（需空额） |
| POST | `/tasks/{id}/retry` | 失败重试 |
| DELETE | `/tasks/{id}` | 移除应用与容器 |
| WS | `/asr/ws` | FunASR 同源代理 |

任务阶段：`Received` → `Analyzing` → `Coding` → `Building` → `Verifying` → `Success` / `Failed`，另有 `Stopped`。

## 额度与生命周期约定

- **占用额度**：仅 `Success`（容器正在运行）
- **上限**：默认 2（`USER_APP_RUNNING_LIMIT`）
- **停止**：保留代码与记录，释放额度，可再启动
- **移除**：删除容器（及可选镜像）、代码目录与任务文档
- **重试**：仅 `Failed`，需有空余运行额度

## PWA 图标

源文件：`docs/icon_source_type.png`。生成到 `frontend/public/`：

```bash
cd frontend && python3 scripts/gen-pwa-icons.py
npm run build
```

产出：`pwa-192.png`、`pwa-512.png`、`pwa-512-maskable.png`、`apple-touch-icon.png`、`favicon-32.png` 等。安装 PWA 前请确保已信任站点证书，否则系统可能回退为字母图标。

## 开发任务进度

见 [docs/development_plan.md](docs/development_plan.md)。

## License

见 [LICENSE](LICENSE)。
