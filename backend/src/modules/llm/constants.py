"""模型 ID 与默认超时（对齐 docs/local_models.md）。"""

QWEN_MODEL_ID = "Qwen3.6-35B-A3B"
SEEDCODER_MODEL_ID = "seedcoder"
EMBEDDING_MODEL_ID = "qwen3-vl-embedding"
RERANKER_MODEL_ID = "qwen3-vl-reranker"
DEEPSEEK_MODEL_ID = "deepseek-r1-70b"

# 文档建议：推理 30–120s；状态探测 8s
DEFAULT_TIMEOUT_SECONDS = 120.0
STATUS_TIMEOUT_SECONDS = 8.0
FUNASR_TIMEOUT_SECONDS = 60.0
