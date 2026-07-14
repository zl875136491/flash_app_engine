"""本地模型客户端公共类型与异常。"""

from __future__ import annotations

from typing import Any

import httpx


class LocalModelError(Exception):
    """本地模型调用失败。"""

    def __init__(self, message: str, *, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class LocalModelHTTPError(LocalModelError):
    pass


def extract_chat_content(payload: dict[str, Any]) -> str:
    try:
        message = payload["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LocalModelError("响应缺少 choices[0].message", body=payload) from exc

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if content is not None and not isinstance(content, str):
        return str(content)

    # 部分推理模型在 thinking 开启时会把正文放进 reasoning，content 为空
    reasoning = message.get("reasoning") or message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning
    return ""


def extract_completion_text(payload: dict[str, Any]) -> str:
    try:
        text = payload["choices"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LocalModelError("响应缺少 choices[0].text", body=payload) from exc
    return text or ""


async def raise_for_model_response(response: httpx.Response) -> Any:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        body: Any
        try:
            body = response.json()
        except Exception:
            body = response.text
        raise LocalModelHTTPError(
            f"模型 HTTP {response.status_code}: {response.url}",
            status_code=response.status_code,
            body=body,
        ) from exc

    try:
        return response.json()
    except Exception as exc:
        raise LocalModelError("响应不是合法 JSON", body=response.text) from exc
