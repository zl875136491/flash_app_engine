"""JSON 提取与解析辅助。"""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    """从模型输出中提取第一个 JSON 对象。"""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("模型返回为空")

    # 去掉 ```json ... ``` 包裹
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.I)
    if fence:
        raw = fence.group(1).strip()

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(raw[start : end + 1])
        if isinstance(data, dict):
            return data

    raise ValueError("无法从模型输出解析 JSON 对象")
