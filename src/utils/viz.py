from __future__ import annotations

import os
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw

from .io import ensure_parent


def save_png(array: np.ndarray, path: str, vmin: float | None = None, vmax: float | None = None, colormap: str = "viridis") -> None:
    ensure_parent(path)
    arr = array.copy()
    if vmin is None:
        vmin = float(np.nanmin(arr)) if np.isfinite(arr).any() else 0.0
    if vmax is None:
        vmax = float(np.nanmax(arr)) if np.isfinite(arr).any() else 1.0
    if vmax == vmin:
        vmax = vmin + 1.0
    norm = (arr - vmin) / (vmax - vmin)
    norm = np.clip(norm, 0, 1)
    rgb = (plt_colormap(colormap)(norm)[..., :3] * 255).astype(np.uint8)
    im = Image.fromarray(rgb)
    im.save(path)


def plt_colormap(name: str):
    import matplotlib.cm as cm
    return cm.get_cmap(name)


def save_blank_tile(path: str, size: int = 256, color: Tuple[int, int, int] = (220, 220, 220), text: str | None = None) -> None:
    ensure_parent(path)
    img = Image.new("RGB", (size, size), color)
    if text:
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), text, fill=(0, 0, 0))
    img.save(path)

