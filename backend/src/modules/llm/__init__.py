"""统一门面：聚合全部本地模型客户端。"""

from __future__ import annotations

from src.modules.llm.deepseek import DeepSeekClient
from src.modules.llm.embedding import EmbeddingClient
from src.modules.llm.funasr import FunASRClient
from src.modules.llm.qwen import QwenClient
from src.modules.llm.reranker import RerankerClient
from src.modules.llm.seedcoder import SeedCoderClient
from src.modules.llm.status import ModelStatusClient


class LocalModelGateway:
    """供编排流水线注入的本地模型入口。"""

    def __init__(self) -> None:
        self.qwen = QwenClient()
        self.seedcoder = SeedCoderClient()
        self.embedding = EmbeddingClient()
        self.reranker = RerankerClient()
        self.deepseek = DeepSeekClient()
        self.funasr = FunASRClient()
        self.status = ModelStatusClient()

    async def aclose(self) -> None:
        for client in (
            self.qwen,
            self.seedcoder,
            self.embedding,
            self.reranker,
            self.deepseek,
            self.status,
        ):
            await client.aclose()


_gateway: LocalModelGateway | None = None


def get_local_model_gateway() -> LocalModelGateway:
    global _gateway
    if _gateway is None:
        _gateway = LocalModelGateway()
    return _gateway
