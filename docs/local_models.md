# 海光 DCU 本地 AI 模型 API 参考

> **文档用途**：供 AI Agent / 自动化脚本快速检索并调用内网部署的大模型服务。  
> **数据来源**：`http://10.17.150.235:30001/map.html`（海光 DCU 全国算力节点分布图）  
> **最后整理**：2026-07-13  
> **网络环境**：所有地址均为内网 IP，需在对应 VPN / 局域网内访问。

---

## 快速索引

| 能力 | 模型 | 节点 | Base URL |
|------|------|------|----------|
| 多模态对话 + OCR | Qwen3.6-35B-A3B | 昆山 | `http://10.8.136.35:8081` |
| 代码生成 | Seed-Coder (8B) | 昆山 | `http://10.8.136.35:8881` |
| 文本/多模态向量 | Qwen3-VL-Embedding | 昆山 | `http://10.8.136.35:8002` |
| 文档重排 | Qwen3-VL-Reranker | 昆山 | `http://10.8.136.35:8003` |
| 深度推理 | DeepSeek-R1-70B | 北京 | `http://10.32.129.214:8000` |
| 实时语音识别 | FunASR | 天津 | `ws://10.17.150.235:10095` |
| 状态监测 | — | 地图服务 | `http://10.17.150.235:30001/api/status` |

---

## 平台概览

```yaml
platform: 海光 DCU 算力池
org: 5000信息系统开发部
map_portal: http://10.17.150.235:30001/map.html
stats:
  deployed_models: 6
  compute_nodes: 5
  online_model_nodes: 3
  total_params: 113B+
```

### 算力节点

| ID | 名称 | 城市 | IP | 状态 | 模型数 |
|----|------|------|-----|------|--------|
| `kunshan` | 昆山算力中心 | 江苏·昆山 | `10.8.136.35` | 在线 | 4 |
| `beijing` | 北京算力中心 | 北京 | `10.32.129.214` | 在线 | 1 |
| `tianjin` | 天津节点 | 天津 | `10.17.150.235` | 在线 | 1 |
| `shenzhen` | 深圳节点 | 广东·深圳 | 待分配 | 待部署 | 0 |
| `hangzhou` | 杭州节点 | 浙江·杭州 | 待分配 | 待部署 | 0 |

---

## 模型 API 详情

### 1. Qwen3.6-35B-A3B（多模态混合推理 + OCR）

```yaml
node: kunshan
host: 10.8.136.35
port: 8081
base_url: http://10.8.136.35:8081
model_id: Qwen3.6-35B-A3B
type: 多模态混合推理
capabilities:
  - 文本对话
  - 图片 OCR（设备面板、实验室标签、实拍照片）
api_style: OpenAI Compatible
endpoints:
  chat: POST /v1/chat/completions
```

**场景一：基础文本对话**

```bash
curl http://10.8.136.35:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3.6-35B-A3B",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下海光DCU服务器。"}
    ],
    "extra_body": {
      "chat_template_kwargs": {"enable_thinking": false}
    }
  }'
```

**场景二：图片 OCR（Python）**

```python
import base64, requests

API_URL = "http://10.8.136.35:8081/v1/chat/completions"
MODEL = "Qwen3.6-35B-A3B"

with open("设备照片.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

response = requests.post(API_URL, json={
    "model": MODEL,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "请识别这张图片中的所有文字"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        ]
    }],
    "temperature": 0.1,
    "max_tokens": 500
})
print(response.json()["choices"][0]["message"]["content"])
```

**请求参数说明**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 固定为 `Qwen3.6-35B-A3B` |
| `messages` | array | 是 | OpenAI 格式消息列表 |
| `messages[].content` | string \| array | 是 | 纯文本或图文混合（`text` + `image_url`） |
| `extra_body.chat_template_kwargs.enable_thinking` | bool | 否 | 是否启用思考链，建议 `false` |
| `temperature` | float | 否 | OCR 场景建议 `0.1` |
| `max_tokens` | int | 否 | 最大输出 token 数 |

---

### 2. Seed-Coder (8B)（代码 LLM）

```yaml
node: kunshan
host: 10.8.136.35
port: 8881
base_url: http://10.8.136.35:8881
model_id: seedcoder
type: 代码LLM
api_style: OpenAI Compatible
endpoints:
  chat: POST /v1/chat/completions
```

```bash
curl -X POST http://10.8.136.35:8881/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "seedcoder",
    "messages": [
      {"role": "user", "content": "你好，请简单介绍一下海光DCU服务器。"}
    ],
    "extra_body": {
      "chat_template_kwargs": {"enable_thinking": false}
    }
  }'
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 固定为 `seedcoder` |
| `messages` | array | 是 | OpenAI 格式对话消息 |
| `extra_body.chat_template_kwargs.enable_thinking` | bool | 否 | 建议 `false` |

---

### 3. Qwen3-VL-Embedding（多模态向量）

```yaml
node: kunshan
host: 10.8.136.35
port: 8002
base_url: http://10.8.136.35:8002
model_id: qwen3-vl-embedding
type: 多模态向量
api_style: OpenAI Compatible
endpoints:
  embeddings: POST /v1/embeddings
```

```bash
curl -X POST http://10.8.136.35:8002/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "人工智能将改变我们的生活方式",
    "model": "qwen3-vl-embedding"
  }'
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 固定为 `qwen3-vl-embedding` |
| `input` | string \| array | 是 | 待向量化的文本 |

---

### 4. Qwen3-VL-Reranker（多模态重排）

```yaml
node: kunshan
host: 10.8.136.35
port: 8003
base_url: http://10.8.136.35:8003
model_id: qwen3-vl-reranker
type: 多模态重排
api_style: 自定义 Rerank
endpoints:
  rerank: POST /v1/rerank
```

```bash
curl -s -X POST http://10.8.136.35:8003/v1/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-vl-reranker",
    "query": "如何配置 Docker 环境",
    "documents": [
      "Docker 安装教程",
      "Python 基础语法",
      "Docker 配置文件详解",
      "Java 编程入门"
    ]
  }'
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 固定为 `qwen3-vl-reranker` |
| `query` | string | 是 | 查询文本 |
| `documents` | string[] | 是 | 待重排的候选文档列表 |

---

### 5. DeepSeek-R1-70B（深度推理 LLM）

```yaml
node: beijing
host: 10.32.129.214
port: 8000
base_url: http://10.32.129.214:8000
model_id: deepseek-r1-70b
type: 推理LLM
capabilities:
  - 复杂逻辑推理
  - 数学问题求解
  - 深度思考
api_style: OpenAI Compatible (Completions)
endpoints:
  completions: POST /v1/completions
```

> **注意**：此模型使用 `/v1/completions`（非 chat），请求体为 `prompt` 而非 `messages`。

```bash
curl http://10.32.129.214:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1-70b",
    "prompt": "甲乙两班共有学生98人，甲班比乙班多6人，求两班各有多少人？",
    "max_tokens": 300,
    "temperature": 0
  }'
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | 固定为 `deepseek-r1-70b` |
| `prompt` | string | 是 | 输入提示词 |
| `max_tokens` | int | 否 | 最大输出 token |
| `temperature` | float | 否 | 推理场景建议 `0` |

---

### 6. FunASR 语音识别（实时流式）

```yaml
node: tianjin
host: 10.17.150.235
port: 10095
ws_url: ws://10.17.150.235:10095
type: 实时语音识别
protocol: WebSocket
audio_format: PCM16, 16kHz, mono
location: 天津二期4层实验室 · TJ-2Q-4F-SYS-C148
```

**协议说明**

| 方向 | 格式 | 说明 |
|------|------|------|
| 客户端 → 服务端 | 二进制 `Int16Array` | PCM16 音频流，采样率 16000Hz，单声道 |
| 客户端 → 服务端 | JSON `{"type": "end"}` | 结束识别信号 |
| 服务端 → 客户端 | JSON `{"text": "..."}` | 实时转写文本 |

**Python 接入示例（伪代码）**

```python
import asyncio, websockets, json

WS_URL = "ws://10.17.150.235:10095"

async def recognize(pcm_chunks):
    async with websockets.connect(WS_URL) as ws:
        for chunk in pcm_chunks:  # chunk: bytes, PCM16 mono 16kHz
            await ws.send(chunk)
        await ws.send(json.dumps({"type": "end"}))
        async for msg in ws:
            data = json.loads(msg)
            print(data.get("text", ""))
```

**选型建议**

- 需要 OCR / 图文理解 → `Qwen3.6-35B-A3B`（昆山 :8081）
- 需要写代码 → `Seed-Coder`（昆山 :8881）
- 需要 RAG 检索 → `Qwen3-VL-Embedding` + `Qwen3-VL-Reranker`（昆山 :8002/:8003）
- 需要复杂推理 / 数学 → `DeepSeek-R1-70B`（北京 :8000）
- 需要语音转文字 → `FunASR`（天津 ws://10.17.150.235:10095）

---

## 管理 / 监测 API

地图门户由 `server.js`（Express）提供，默认端口 3000，当前部署在 `30001`。

### GET `/api/status`

获取各节点模型的实时在线状态（每 30 秒探测一次）。

```
GET http://10.17.150.235:30001/api/status
Content-Type: application/json
```

**响应示例**

```json
[
  {
    "id": "kunshan",
    "name": "昆山算力中心",
    "location": "昆山数据中心",
    "models": [
      {
        "name": "Qwen3.6-35B-A3B",
        "type": "多模态混合推理",
        "port": ":8081",
        "status": "online",
        "latency": 126,
        "error": "",
        "lastCheck": "2026/7/13 06:36:01",
        "nodeId": "kunshan",
        "nodeName": "昆山算力中心"
      }
    ]
  }
]
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | `online` \| `offline` \| `error` \| `pending` |
| `latency` | int | 探测延迟（ms），`-1` 表示未探测 |
| `error` | string | 错误信息，正常为空 |
| `lastCheck` | string | 上次探测时间 |

### GET `/api/status/sse`

Server-Sent Events 实时推送状态变更。

```
GET http://10.17.150.235:30001/api/status/sse
Accept: text/event-stream
```

推送格式：`data: <JSON 同 /api/status>\n\n`

### 静态资源

| 路径 | 说明 |
|------|------|
| `/` | 重定向至 `/map.html` |
| `/map.html` | 算力节点分布可视化页面 |
| `/china-map-data.js` | 中国地图 GeoJSON 数据 |

---

## AI Agent 使用指南

### 选择模型的决策树

```
需要处理图片/OCR？
  └─ 是 → Qwen3.6-35B-A3B (昆山:8081)
需要生成/补全代码？
  └─ 是 → Seed-Coder (昆山:8881)
需要语义检索/RAG？
  ├─ 向量化 → Qwen3-VL-Embedding (昆山:8002)
  └─ 重排序 → Qwen3-VL-Reranker (昆山:8003)
需要复杂推理/数学？
  └─ 是 → DeepSeek-R1-70B (北京:8000)
需要语音转文字？
  └─ 是 → FunASR WebSocket (天津:10095)
```

### 通用约定

1. **Content-Type**：所有 HTTP API 均使用 `application/json`
2. **超时建议**：模型推理接口建议设置 30–120s 超时；状态探测为 8s
3. **认证**：当前无需 API Key / Token
4. **网络**：必须在能访问 `10.x.x.x` 段的内网环境
5. **健康检查**：调用前先 `GET /api/status` 确认目标模型 `status == "online"`

### 典型 RAG 流水线

```
用户 query
  → Qwen3-VL-Embedding (/v1/embeddings) 向量化 query + 文档库
  → 向量相似度初筛 top-K
  → Qwen3-VL-Reranker (/v1/rerank) 精排
  → Qwen3.6-35B-A3B (/v1/chat/completions) 生成最终回答
```

### 错误处理

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 连接超时 | 节点离线或网络不通 | 查 `/api/status`，换节点或重试 |
| HTTP 4xx/5xx | 请求体格式错误 | 核对 `model` 字段和 endpoint 路径 |
| DeepSeek 无响应 | 用了 chat 接口 | 改用 `/v1/completions` + `prompt` |
| FunASR 乱码 | 音频格式不对 | 确保 PCM16、16kHz、单声道 |

---

## 附录：完整端点清单

| # | 方法 | URL | 模型 | 用途 |
|---|------|-----|------|------|
| 1 | POST | `http://10.8.136.35:8081/v1/chat/completions` | Qwen3.6-35B-A3B | 对话 / OCR |
| 2 | POST | `http://10.8.136.35:8881/v1/chat/completions` | seedcoder | 代码生成 |
| 3 | POST | `http://10.8.136.35:8002/v1/embeddings` | qwen3-vl-embedding | 向量嵌入 |
| 4 | POST | `http://10.8.136.35:8003/v1/rerank` | qwen3-vl-reranker | 文档重排 |
| 5 | POST | `http://10.32.129.214:8000/v1/completions` | deepseek-r1-70b | 深度推理 |
| 6 | WS | `ws://10.17.150.235:10095` | FunASR | 实时语音识别 |
| 7 | GET | `http://10.17.150.235:30001/api/status` | — | 模型状态查询 |
| 8 | GET | `http://10.17.150.235:30001/api/status/sse` | — | 状态 SSE 推送 |
