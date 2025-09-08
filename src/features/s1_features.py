from __future__ import annotations

import os
import numpy as np

from ..utils.io import ensure_dir


def compute_s1_features(out_dir: str, shape: tuple[int, int] = (256, 256)) -> dict[str, str]:
    ensure_dir(out_dir)
    h, w = shape
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    vv = (0.1 + 0.05 * np.sin(4 * np.pi * xx)).astype(np.float32)
    vh = (0.05 + 0.03 * np.cos(4 * np.pi * yy)).astype(np.float32)
    ratio = np.divide(vv, np.maximum(vh, 1e-3)).astype(np.float32)
    outputs: dict[str, str] = {}
    for name, arr in {"vv": vv, "vh": vh, "vv_vh": ratio}.items():
        path = os.path.join(out_dir, f"{name}.npy")
        np.save(path, arr)
        outputs[name] = path
    return outputs

