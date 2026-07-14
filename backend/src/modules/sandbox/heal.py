"""编译/运行失败时的一次自愈（Seed-Coder）。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.modules.llm import LocalModelGateway
from src.modules.worker.coding import write_code_bundle
from src.modules.worker.jsonutil import extract_json_object
from src.modules.worker.prompts import CODE_SYSTEM

logger = logging.getLogger(__name__)


HEAL_INSTRUCTION = """
上一次 Docker 构建或运行验证失败。请根据错误日志修复代码，并输出完整 files JSON
（覆盖原文件）。只输出 JSON，不要 Markdown。
""".strip()


async def heal_generated_code(
    *,
    task_id: str,
    code_root: str,
    error_log: str,
    gateway: LocalModelGateway,
    mock: bool = False,
) -> str:
    root = Path(code_root)
    snippets: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.stat().st_size > 80_000:
            continue
        rel = path.relative_to(root).as_posix()
        try:
            snippets.append(f"## {rel}\n{path.read_text(encoding='utf-8', errors='ignore')[:4000]}")
        except Exception:
            continue
        if len(snippets) >= 12:
            break

    if mock:
        # mock 自愈：确保有可服务的 index 与健康页
        frontend = root / "frontend" / "index.html"
        frontend.parent.mkdir(parents=True, exist_ok=True)
        frontend.write_text(
            "<!doctype html><html><body><h1>healed</h1><p>ok</p></body></html>\n",
            encoding="utf-8",
        )
        health = root / "frontend" / "health"
        health.write_text("ok\n", encoding="utf-8")
        logger.info("mock heal wrote frontend health page")
        return code_root

    prompt = (
        f"{HEAL_INSTRUCTION}\n\n"
        f"错误日志：\n{error_log[:6000]}\n\n"
        f"当前代码摘录：\n{chr(10).join(snippets)}\n"
    )
    text = await gateway.seedcoder.chat(
        [
            {"role": "system", "content": CODE_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        enable_thinking=False,
        temperature=0.1,
        max_tokens=4096,
    )
    bundle: dict[str, Any] = extract_json_object(text)
    if not bundle.get("files"):
        raise ValueError("自愈结果缺少 files")
    return write_code_bundle(task_id, bundle)
