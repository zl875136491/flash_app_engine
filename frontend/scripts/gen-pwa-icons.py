#!/usr/bin/env python3
"""从 docs/icon_source_type.png 生成 PWA 图标到 frontend/public/。"""
from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs" / "icon_source_type.png"
OUT = ROOT / "frontend" / "public"


def main() -> None:
    im = Image.open(SRC).convert("RGBA")
    w, h = im.size
    pixels = im.load()
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 200:
                continue
            if g > 70 and g < 160 and r < 90 and b < 100 and (g - r) > 30:
                xs.append(x)
                ys.append(y)
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    side = int(max(x1 - x0, y1 - y0) * 1.01)
    x0s = max(0, min(int(round(cx - side / 2)), w - side))
    y0s = max(0, min(int(round(cy - side / 2)), h - side))
    crop = im.crop((x0s, y0s, x0s + side, y0s + side))

    outputs = [
        (192, "pwa-192.png"),
        (512, "pwa-512.png"),
        (512, "pwa-512-maskable.png"),
        (180, "apple-touch-icon.png"),
        (32, "favicon-32.png"),
    ]
    for size, name in outputs:
        path = OUT / name
        crop.resize((size, size), Image.Resampling.LANCZOS).save(
            path, "PNG", optimize=True, compress_level=9
        )
        print("wrote", path)

    if shutil.which("pngquant"):
        for _, name in outputs[:-1]:
            path = OUT / name
            subprocess.run(
                ["pngquant", "--force", "--quality=70-95", "--skip-if-larger", "--output", str(path), str(path)],
                check=False,
            )


if __name__ == "__main__":
    main()
