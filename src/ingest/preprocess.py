from __future__ import annotations

import os
from typing import Dict

import numpy as np
import xarray as xr

from ..utils.io import ensure_dir


def synthetic_scene(width: int = 256, height: int = 256, bands: Dict[str, float] | None = None) -> xr.Dataset:
    if bands is None:
        bands = {"B02": 0.1, "B03": 0.15, "B04": 0.2, "B08": 0.6, "SCL": 5}
    y = np.linspace(0, 1, height)
    x = np.linspace(0, 1, width)
    xx, yy = np.meshgrid(x, y)
    data_vars = {}
    for b, base in bands.items():
        arr = (base + 0.1 * np.sin(2 * np.pi * xx) * np.cos(2 * np.pi * yy)).astype(np.float32)
        data_vars[b] = (("y", "x"), arr)
    ds = xr.Dataset(data_vars=data_vars, coords={"y": y, "x": x})
    return ds


def preprocess_to_interim(aoi_path: str, raw_dir: str, interim_dir: str) -> str:
    # Offline synthetic dataset
    ensure_dir(interim_dir)
    out_nc = os.path.join(interim_dir, "synthetic_s2.nc")
    ds = synthetic_scene()
    ds.to_netcdf(out_nc)
    return out_nc

