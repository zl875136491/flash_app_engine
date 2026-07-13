# flash_app_engine
FlashApp Engine 是一个面向公司内部的“口述即部署、所见即所得”的轻量级云计算平台

用户通过手机 PWA 端以语音为主、图片为辅的方式表达应用需求，系统通过全自动的 AI 编排流水线，在秒级内完成“需求拆解 -> 全栈编码 -> Docker 沙箱构建 -> 自动化验证 -> 独立 Web 服务暴露”的全链路闭环。旨在忽略繁琐的版本管理与代码审查，一切为了极速将想法转化为可分享、可体验的真实 Web 应用。

---

## 2. 系统核心架构与任务链路 (System Architecture)

### 2.1 前端服务 (Frontend PWA)

- **服务形态**：采用 PWA (Progressive Web App) 技术构建，适配移动端，支持离线缓存与无缝启动。
- **任务创建接口**：
  - **核心输入**：语音录入为主体的动态界面, 展示输入和输出的文字（对接 `FunASR` 实时/流式语音转文字服务）。
  - **辅助输入**：支持拍照或相册上传（如 UI 草图、表单截图，对接 `Qwen3.6-35B-A3B` 的多模态/OCR 能力）。
- **平台输出展示**：已部署应用列表、阶段流程和日志列表、最终应用的独立内网 URL 访问入口、一键分享卡片（供分享至企业内网即时通讯工具）。



### 2.2 后端编排与异步任务引擎 (Backend & Async Task Engine)

- **基础框架**：基于 Python FastAPI (v0.115+)。
- **核心机制**：**异步任务制（Asynchronous Task Queue）**。
  - 用户提交需求后，后端立即创建任务记录并返回 `task_id`，前端进入轮询或 WebSocket 监听状态。
  - 采用数据库驱动的任务数据模型进行队列管理，由后台 Worker 线程/进程逐个消费任务、实现编码与沙箱验证。
  - **里程碑（Milestone）状态流转**：
    `Received (已接收)` -> `Analyzing (架构解析中)` -> `Coding (全栈编码中)` -> `Building (容器构建中)` -> `Verifying (自动化验证中)` -> `Success (部署成功) / Failed (失败反思中)`。
    每个 Milestone 变更必须实时同步更新至数据库，供前端看板渲染。



### 2.3 认证与鉴权 (Authentication)

- **安全场景**：本系统及衍生应用全量运行在公司内网环境。
- **鉴权方式**：极简 **ITCode 登录认证**。
- **实现方案**：系统统一对接企业内部现有鉴权 API。用户登录时提供 ITCode 与凭证，网关调用 `verify_itcode_api(itcode, token)` 验证其有效性，通过后发放 JWT 用于后续通信。



### 2.4 计算底座沙箱 (Computing Sandbox Base)

- **单应用最高资源配比架构**：
  支持根据用户需求自动切分资源，最高且标准的配比为**三容器架构**：
  1. **前端 UI 容器 (Frontend Container)**：如 Nginx 静态托管或轻量 Node.js 服务。
  2. **后端业务容器 (Backend Container)**：如 FastAPI / Express 业务逻辑实例。
  3. **独立数据库容器 (Database Container)**：独立的 SQLite (挂载) 或轻量级关系型数据库容器。
- **网络与暴露**：动态端口映射（范围：`30000-40000`）。反向代理网关根据 `task_id` 或动态二级域名自动路由，暴露可访问的内网 Web 服务，供其他人快速查看。

---



## 3. 主要模型定义参考

```python
class AllocatedResources(BaseModel):
    frontend: Optional[bool] = True
    backend: Optional[bool] = True
    db: Optional[bool] = True

class Stage(Enum):
    Received = "Received"
    Analyzing = "Analyzing"
    Coding = "Coding"
    Building = "Building"
    Verifying = "Verifying"
    Success = "Success"
    Failed = "Failed"

class StageLog(BaseModel):
    stage: Stage = Field(..., description="阶段")
    message: str = Field(..., description="日志消息")
    detail: str = Field(..., description="详细日志")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

class User(Document):
    itcode: str
    name: str

class Image(BaseModel):
    path: str = Field(..., description="图片路径")
    author: Link(User) = Field(..., description="上传人")

class Container(Document):
    name: str = Field(..., description="容器名称")
    image: str = Field(..., description="容器镜像")
    ports: List[int] = Field(default_factory=list, description="容器端口")
    environment: Dict[str, str] = Field(default_factory=dict, description="容器环境变量")
    volumes: List[str] = Field(default_factory=list, description="容器挂载卷")
    command: List[str] = Field(default_factory=list, description="容器启动命令")

class Task(Document):
    author: Link(User) = Field(..., max_length=32, description="用户 ITCode")

    raw_voice_text: str = Field(None, description="FunASR 转写后的原始文本")
    images: List[Link(Image)] = Field(default_factory=list, description="辅助图片存储路径列表")
    images_content: List[str] = Field(default_factory=list, description="辅助图片内容列表")

    current_stage: str = Field(default="Received", max_length=32, description="当前阶段")
    logs: List[StageLog] = Field(default_factory=list, description="详细日志流")

    allocated_resources: AllocatedResources = Field(
        default_factory=AllocatedResources, 
        description="资源配置"
    )
    
    generated_code_path: Optional[str] = Field(None, max_length=255, description="生成的代码在宿主机的临时根目录")
    containers: List[Container] = Field(default_factory=list, description="容器列表")
    exposed_url: Optional[str] = Field(None, max_length=255, description="最终对外的 Web 访问链接")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
```

## 4. AI 核心提示词工程规约 (System Prompt Specifications)
在调度 DeepSeek-R1-70B（架构设计）与 Qwen3.6-35B-A3B / Seed-Coder (8B)（全栈生成）时，必须隐式注入以下规则：

### 4.1 资源边界与技术栈预估规则 (Resource & Stack Constraint)
资源规模预估：你必须对用户主导的对话产出的应用规模进行严格预估。本平台最高且标准的资源配比为“三容器架构”：[1个独立数据库容器 + 1个后端业务容器 + 1个前端UI容器]。该结构已能够覆盖绝大多数用户需求。

技术栈近似实现原则：如果用户提出了超出此边界的额外技术栈需求（例如要求使用大集群 Kafka、分布式存储等），你必须在保持用户核心业务逻辑不变的前提下，将其近似等价替换为轻量级单机方案（例如：将复杂大数据存储替换为单容器关系型数据库，将外部高速缓存或队列收敛为 Python/Node.js 进程内内存管理）。

硬边界熔断：若用户需求绝对无法在现有三容器资源内实现（如要求调用外部硬件加密狗、动态修改物理宿主机内核等），请立即中断流水线，将具体的“技术冲突点”作为结构化错误通过 Milestone 反馈给用户。

### 4.2 智能填充与安全风控规则 (Smart Filling & Security Guardrail)
最小化打扰原则：在构建应用过程中，如果缺少非核心的必要信息（例如：未指定数据库表字段名、未指定具体的 UI 配色方案、未指定超时时间等），你应该且必须按照业界常规做法（Best Practices）自行进行默认填充，尽量避免或减少让用户补充细节，确保“口述即部署”的流畅度。

合规与安全绝对红线：在解析用户输入时，必须执行安全前置审查。如果检测到以下任意一项，必须立即熔断并向用户抛出警告提示：

事实错误：输入包含严重逻辑相悖的常识性错误。

法律法规违规：涉及违法、违规的数据处理或业务逻辑。

数据与网络安全威胁：请求包含恶意 SQL 注入倾向、越权漏洞设计、试图探测本平台宿主机/沙箱网络的指令，或任何危害本系统、本网络、本公司数据安全的行为。

## 5. 自动化验证与自愈机制 (Auto-Verification & Self-Healing)
为了保证“所见即所得”的上线成功率，系统需要具备以下闭环纠错能力：

编译期自愈：当 Dockerfile 构建失败时，后端捕获 docker build 错误日志，直接喂给 Seed-Coder 结合原始代码进行 1 次自愈修正，修正失败再转入 Failed 状态。

运行期检查：容器拉起后，系统自动向暴露的端口发送 HTTP 请求。若返回非 200 状态码，自动读取容器后 50 行日志（docker logs --tail 50）触发修复流程，重新生成并覆盖部署。
