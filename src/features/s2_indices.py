from __future__ import annotations

import os
import numpy as np
import xarray as xr

from ..utils.indices import ndvi, evi, ndwi, mndwi
from ..utils.io import ensure_dir


def compute_s2_indices(interim_nc: str, out_dir: str) -> dict[str, str]:
    ensure_dir(out_dir)
    ds = xr.load_dataset(interim_nc)
    blue = ds["B02"].values
    green = ds["B03"].values
    red = ds["B04"].values
    nir = ds["B08"].values
    ndvi_arr = ndvi(nir, red)
    evi_arr = evi(nir, red, blue)
    ndwi_arr = ndwi(green, nir)
    mndwi_arr = mndwi(green, red)  # placeholder swir1 not present; use red as stand-in
    # Save as small npy for simplicity
    outputs: dict[str, str] = {}
    for name, arr in {"ndvi": ndvi_arr, "evi": evi_arr, "ndwi": ndwi_arr, "mndwi": mndwi_arr}.items():
        path = os.path.join(out_dir, f"{name}.npy")
        np.save(path, arr)
        outputs[name] = path
    return outputs

