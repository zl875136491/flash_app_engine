"""模型在线状态探测（地图服务 /api/status）。"""

from __future__ import annotations

from typing import Any

from src.configs import get_settings
from src.modules.llm.base import HttpModelClient
from src.modules.llm.constants import STATUS_TIMEOUT_SECONDS


class ModelStatusClient(HttpModelClient):
    def __init__(
        self,
        *,
        status_url: str | None = None,
        timeout: float = STATUS_TIMEOUT_SECONDS,
        client=None,
    ):
        settings = get_settings()
        url = status_url or settings.model_status_url
        # base_url 仅作占位；状态接口使用绝对 URL
        super().__init__(
            base_url=url.rsplit("/", 1)[0],
            model_id="status",
            timeout=timeout,
            client=client,
        )
        self.status_url = url

    async def fetch_status(self) -> list[dict[str, Any]]:
        data = await self._get_json(self.status_url)
        if not isinstance(data, list):
            return [data]
        return data

    async def is_model_online(self, model_name: str) -> bool:
        nodes = await self.fetch_status()
        target = model_name.lower()
        for node in nodes:
            for model in node.get("models", []) or []:
                name = str(model.get("name", "")).lower()
                if name == target or target in name:
                    return str(model.get("status", "")).lower() == "online"
        return False
