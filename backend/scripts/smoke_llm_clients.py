"""本地模型客户端离线冒烟测试（httpx MockTransport，不访问内网）。"""

from __future__ import annotations

import asyncio
import json

import httpx

from src.modules.llm.deepseek import DeepSeekClient
from src.modules.llm.embedding import EmbeddingClient
from src.modules.llm.qwen import QwenClient
from src.modules.llm.reranker import RerankerClient
from src.modules.llm.seedcoder import SeedCoderClient
from src.modules.llm.status import ModelStatusClient


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("/v1/chat/completions"):
        body = json.loads(request.content.decode())
        model = body.get("model")
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": f"ok:{model}"}}
                ]
            },
        )
    if path.endswith("/v1/completions"):
        return httpx.Response(
            200,
            json={"choices": [{"text": "answer:42"}]},
        )
    if path.endswith("/v1/embeddings"):
        return httpx.Response(
            200,
            json={"data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]},
        )
    if path.endswith("/v1/rerank"):
        return httpx.Response(
            200,
            json={"results": [{"index": 0, "relevance_score": 0.9}]},
        )
    if path.endswith("/api/status"):
        return httpx.Response(
            200,
            json=[
                {
                    "id": "kunshan",
                    "models": [
                        {"name": "Qwen3.6-35B-A3B", "status": "online"},
                        {"name": "seedcoder", "status": "offline"},
                    ],
                }
            ],
        )
    return httpx.Response(404, json={"error": "not found"})


async def main() -> None:
    transport = httpx.MockTransport(_handler)
    async with httpx.AsyncClient(transport=transport) as shared:
        qwen = QwenClient(base_url="http://qwen.test", client=shared)
        seed = SeedCoderClient(base_url="http://seed.test", client=shared)
        emb = EmbeddingClient(base_url="http://emb.test", client=shared)
        rerank = RerankerClient(base_url="http://rerank.test", client=shared)
        deep = DeepSeekClient(base_url="http://deep.test", client=shared)
        status = ModelStatusClient(
            status_url="http://status.test/api/status",
            client=shared,
        )

        assert await qwen.chat([{"role": "user", "content": "hi"}]) == "ok:Qwen3.6-35B-A3B"
        assert await seed.generate_code("print(1)") == "ok:seedcoder"
        assert await emb.embed("hello") == [[0.1, 0.2, 0.3]]
        assert (await rerank.rerank(query="q", documents=["a"]))["results"][0]["index"] == 0
        assert await deep.complete("1+1=?") == "answer:42"
        assert await status.is_model_online("Qwen3.6-35B-A3B") is True
        assert await status.is_model_online("seedcoder") is False

        ocr = await qwen.ocr(image_bytes=b"fake-image-bytes", mime_type="image/jpeg")
        assert ocr.startswith("ok:")

    print("llm client smoke tests passed")


if __name__ == "__main__":
    asyncio.run(main())
