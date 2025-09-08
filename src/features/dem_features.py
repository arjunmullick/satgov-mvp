from __future__ import annotations

import os
import numpy as np

from ..utils.io import ensure_dir


def compute_dem_features(out_dir: str, shape: tuple[int, int] = (256, 256)) -> dict[str, str]:
    ensure_dir(out_dir)
    h, w = shape
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xx, yy = np.meshgrid(x, y)
    z = (100 + 10 * xx + 5 * yy).astype(np.float32)
    dzdx = np.gradient(z, axis=1)
    dzdy = np.gradient(z, axis=0)
    slope = np.hypot(dzdx, dzdy).astype(np.float32)
    aspect = np.arctan2(dzdy, dzdx).astype(np.float32)
    out = {}
    for name, arr in {"elev": z, "slope": slope, "aspect": aspect}.items():
        path = os.path.join(out_dir, f"{name}.npy")
        np.save(path, arr)
        out[name] = path
    return out

