from __future__ import annotations

import os
from typing import Dict

import numpy as np
import pandas as pd

from ..utils.io import ensure_dir


def aggregate_to_parcels(parcel_ids: np.ndarray, rasters: Dict[str, np.ndarray]) -> pd.DataFrame:
    # parcel_ids: HxW integers assigning each pixel to parcel id (or -1 for none)
    ids = np.unique(parcel_ids)
    ids = ids[ids >= 0]
    rows = []
    for pid in ids:
        mask = parcel_ids == pid
        row = {"id": int(pid)}
        for name, arr in rasters.items():
            vals = arr[mask]
            if vals.size == 0:
                row[f"{name}_p50"] = np.nan
                row[f"{name}_p90"] = np.nan
                row[f"{name}_mean"] = np.nan
                row[f"{name}_std"] = np.nan
            else:
                row[f"{name}_p50"] = float(np.nanpercentile(vals, 50))
                row[f"{name}_p90"] = float(np.nanpercentile(vals, 90))
                row[f"{name}_mean"] = float(np.nanmean(vals))
                row[f"{name}_std"] = float(np.nanstd(vals))
        rows.append(row)
    return pd.DataFrame(rows).sort_values("id").reset_index(drop=True)


def save_features(df: pd.DataFrame, out_path: str) -> str:
    ensure_dir(os.path.dirname(out_path) or ".")
    df.to_csv(out_path, index=False)
    return out_path

