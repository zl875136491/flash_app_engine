"""安全前置审查：规则熔断 + 结构化结果。"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SafetyResult:
    ok: bool
    reason: str = ""
    category: str = ""  # security | hard_boundary | fact


_SECURITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "网络安全威胁",
        re.compile(
            r"(sql\s*注入|union\s+select|drop\s+table|rm\s+-rf|/\.ssh|docker\.sock|"
            r"读取宿主机|探测内网|扫描端口|反弹shell|越权漏洞|窃取(密码|token|密钥))",
            re.I,
        ),
    ),
    (
        "法律法规违规",
        re.compile(r"(贩毒|诈骗|洗钱|窃取公民|伪造证件|违法赌博)", re.I),
    ),
]

_HARD_BOUNDARY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "硬边界冲突",
        re.compile(
            r"(硬件加密狗|修改(物理)?内核|加载内核模块|直通GPU集群|多机Kafka集群|"
            r"分布式存储集群|改写宿主机系统)",
            re.I,
        ),
    ),
]


def build_requirement_text(
    *,
    raw_voice_text: str | None,
    images_content: list[str] | None,
) -> str:
    parts: list[str] = []
    if raw_voice_text:
        parts.append(raw_voice_text.strip())
    for item in images_content or []:
        if item and item.strip():
            parts.append(item.strip())
    return "\n".join(parts).strip()


def precheck_requirement(text: str) -> SafetyResult:
    """对用户输入做本地规则审查；命中则立即熔断。"""
    if not text.strip():
        return SafetyResult(ok=False, reason="需求文本为空", category="fact")

    for category, pattern in _SECURITY_PATTERNS:
        match = pattern.search(text)
        if match:
            return SafetyResult(
                ok=False,
                reason=f"{category}：检测到高风险表述「{match.group(0)}」",
                category="security",
            )

    for category, pattern in _HARD_BOUNDARY_PATTERNS:
        match = pattern.search(text)
        if match:
            return SafetyResult(
                ok=False,
                reason=f"{category}：超出三容器硬边界「{match.group(0)}」",
                category="hard_boundary",
            )

    return SafetyResult(ok=True)
