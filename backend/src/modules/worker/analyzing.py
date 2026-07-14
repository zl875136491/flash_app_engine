"""Analyzing 阶段：架构解析（DeepSeek-R1）。"""

from __future__ import annotations

import logging
from typing import Any

from src.modules.llm import LocalModelGateway
from src.modules.models.enums import AllocatedResources
from src.modules.worker.jsonutil import extract_json_object
from src.modules.worker.prompts import ANALYZE_SYSTEM

logger = logging.getLogger(__name__)


def mock_architecture(requirement: str) -> dict[str, Any]:
    return {
        "safe": True,
        "hard_boundary_violation": False,
        "violation_reason": None,
        "security_violation": False,
        "security_reason": None,
        "summary": f"轻量应用：{requirement[:80]}",
        "allocated_resources": {"frontend": True, "backend": True, "db": True},
        "tech_stack": {
            "frontend": "静态 HTML + Nginx",
            "backend": "FastAPI",
            "db": "SQLite",
        },
        "approx_replacements": [],
        "modules": ["health", "items"],
        "api_outline": ["GET /health", "GET /api/items", "POST /api/items"],
    }


async def analyze_requirement(
    requirement: str,
    *,
    gateway: LocalModelGateway,
    mock: bool = False,
) -> dict[str, Any]:
    if mock:
        return mock_architecture(requirement)

    prompt = (
        f"{ANALYZE_SYSTEM}\n\n"
        f"用户需求：\n{requirement}\n\n"
        "请只输出 JSON。"
    )

    # Qwen 作为主解析器（稳定 JSON）；DeepSeek 退化/不可用时再尝试
    try:
        text = await gateway.qwen.chat(
            [{"role": "user", "content": prompt}],
            enable_thinking=False,
            temperature=0,
            max_tokens=1200,
        )
        data = extract_json_object(text)
        logger.info("analyze via qwen summary=%s", data.get("summary"))
        return data
    except Exception as exc:
        logger.warning("qwen analyze failed, fallback to deepseek: %s", exc)

    text = await gateway.deepseek.complete(prompt, max_tokens=2048, temperature=0)
    data = extract_json_object(text)
    logger.info("analyze via deepseek summary=%s", data.get("summary"))
    return data


def resources_from_plan(plan: dict[str, Any]) -> AllocatedResources:
    raw = plan.get("allocated_resources") or {}
    return AllocatedResources(
        frontend=bool(raw.get("frontend", True)),
        backend=bool(raw.get("backend", True)),
        db=bool(raw.get("db", True)),
    )
