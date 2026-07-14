"""JSON 提取与解析辅助。"""

from __future__ import annotations

import json
import re
from typing import Any

_THINK_BLOCK = re.compile(r"<think>[\s\S]*?</think>", re.I)
_FENCE_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.I)


def _strip_model_noise(text: str) -> str:
    raw = (text or "").strip()
    raw = _THINK_BLOCK.sub("", raw).strip()
    fence = _FENCE_BLOCK.search(raw)
    if fence:
        raw = fence.group(1).strip()
    return raw


def extract_json_object(text: str) -> dict[str, Any]:
    """从模型输出中提取第一个 JSON 对象。"""
    raw = _strip_model_noise(text)
    if not raw:
        raise ValueError("模型返回为空")

    # 退化输出（如全是 ! / 标点）直接失败，便于上层回退
    alnum = sum(1 for ch in raw if ch.isalnum())
    if alnum < 3 and "{" not in raw:
        raise ValueError("模型返回无有效内容")

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(raw[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    raise ValueError("无法从模型输出解析 JSON 对象")
