"""计算底座沙箱：构建、端口映射、验证与自愈。"""

from __future__ import annotations

__all__ = ["build_and_verify"]


def __getattr__(name: str):
    if name == "build_and_verify":
        from src.modules.sandbox.service import build_and_verify

        return build_and_verify
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
