"""动态端口分配（30000–40000）。"""

from __future__ import annotations

import socket

from src.configs import get_settings


def allocate_host_port(
    *,
    port_min: int | None = None,
    port_max: int | None = None,
) -> int:
    settings = get_settings()
    low = port_min if port_min is not None else settings.sandbox_port_min
    high = port_max if port_max is not None else settings.sandbox_port_max
    if low > high:
        raise ValueError("无效端口范围")

    for port in range(low, high + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"端口池已耗尽: {low}-{high}")
