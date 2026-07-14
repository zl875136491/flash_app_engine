"""从 docs/auth_users.md 加载允许登录的 ITCode 白名单。"""

from __future__ import annotations

import ast
import logging
import re
from functools import lru_cache
from pathlib import Path

from src import APP_ROOT

logger = logging.getLogger(__name__)

# 与 docs/auth_users.md 保持同步的兜底列表（文档解析失败时使用）
_FALLBACK_ITCODES: frozenset[str] = frozenset(
    {
        "zhangle",
        "wangyy1",
        "liushuang",
        "wenyy",
        "zhaodk",
        "litq",
        "libiao1",
        "liujl7",
        "zhanglei8",
    }
)


def _auth_users_path() -> Path:
    # APP_ROOT = backend/；文档在仓库根 docs/
    return Path(APP_ROOT).resolve().parent / "docs" / "auth_users.md"


def _parse_itcodes_from_markdown(text: str) -> set[str]:
    """解析 auth_users.md 中的 Python 列表赋值。"""
    match = re.search(r"itcodes\s*=\s*(\[[\s\S]*?\])", text)
    if not match:
        raise ValueError("auth_users.md 中未找到 itcodes 列表")
    values = ast.literal_eval(match.group(1))
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ValueError("itcodes 必须是字符串列表")
    return {v.strip().lower() for v in values if v.strip()}


@lru_cache
def get_allowed_itcodes() -> frozenset[str]:
    path = _auth_users_path()
    try:
        text = path.read_text(encoding="utf-8")
        codes = frozenset(_parse_itcodes_from_markdown(text))
        if not codes:
            raise ValueError("itcodes 为空")
        logger.info("Loaded %d ITCodes from %s", len(codes), path)
        return codes
    except Exception as exc:
        logger.warning(
            "Failed to load ITCodes from %s (%s); using fallback allowlist",
            path,
            exc,
        )
        return _FALLBACK_ITCODES


def is_allowed_itcode(itcode: str) -> bool:
    normalized = (itcode or "").strip().lower()
    if not normalized:
        return False
    return normalized in get_allowed_itcodes()
