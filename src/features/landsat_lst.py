from __future__ import annotations

import os
import numpy as np

from ..utils.io import ensure_dir


def compute_lst_proxy(out_dir: str, shape: tuple[int, int] = (256, 256)) -> str:
    ensure_dir(out_dir)
    h, w = shape
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    lst = (300 + 5 * np.sin(2 * np.pi * xx) * np.cos(2 * np.pi * yy)).astype(np.float32)
    path = os.path.join(out_dir, "lst_proxy.npy")
    np.save(path, lst)
    return path

