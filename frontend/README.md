# FlashApp Frontend

移动端优先的 PWA 前端（任务点 9 脚手架）。

## 技术栈

- React 19 + Vite 7
- Tailwind CSS v4（`@tailwindcss/vite`）
- shadcn/ui（`components.json` + `src/components/ui`）
- `vite-plugin-pwa`
- 主题唯一来源：`src/index.css`

## 开发

```bash
cd frontend
npm install
npm run dev
```

API 代理：`/api` → `http://127.0.0.1:8000`

## 认证

- 登录页：`/login`（ITCode，对接 `POST /api/v1/auth/login`）
- 登录后壳层：顶部品牌栏 + 底部「创建 / 应用」Tab
- Token 存 `localStorage`，启动时调用 `/api/v1/auth/me` 恢复会话

## 创建任务

- `/create`：语音（FunASR PCM16）+ 图片上传 + 文本编辑后提交
- `POST /api/v1/uploads/images`、`POST /api/v1/tasks`
- FunASR 地址：`VITE_FUNASR_WS_URL`（默认内网 `ws://10.17.150.235:10095`）

## 构建

```bash
npm run build
npm run preview
```
