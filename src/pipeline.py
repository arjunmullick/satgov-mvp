from __future__ import annotations

import os
import json
import numpy as np
import geopandas as gpd

from .config import settings
from .utils.io import ensure_dir
from .utils.viz import save_blank_tile, save_png
from .ingest.preprocess import preprocess_to_interim
from .features.s2_indices import compute_s2_indices
from .features.s1_features import compute_s1_features
from .features.dem_features import compute_dem_features
from .features.featurize import aggregate_to_parcels, save_features
from .models.irrigate_clf import train_or_load, predict
from .models.water_anomaly import score_water_anomaly


def synthetic_parcel_ids(h: int, w: int, n_x: int = 8, n_y: int = 8) -> np.ndarray:
    ids = -np.ones((h, w), dtype=np.int32)
    sx, sy = w // n_x, h // n_y
    pid = 0
    for j in range(n_y):
        for i in range(n_x):
            xs = i * sx
            xe = (i + 1) * sx
            ys = j * sy
            ye = (j + 1) * sy
            ids[ys:ye, xs:xe] = pid
            pid += 1
    return ids


def run_offline_pipeline(aoi_path: str, start: str, end: str) -> dict:
    # Prepare dirs
    ensure_dir(settings.raw_dir)
    ensure_dir(settings.interim_dir)
    ensure_dir(settings.features_dir)
    ensure_dir(settings.models_dir)
    ensure_dir(settings.tiles_dir)

    # Preprocess -> synthetic
    interim_nc = preprocess_to_interim(aoi_path, settings.raw_dir, settings.interim_dir)

    # Indices/features
    s2_paths = compute_s2_indices(interim_nc, os.path.join(settings.interim_dir, "s2"))
    s1_paths = compute_s1_features(os.path.join(settings.interim_dir, "s1"))
    dem_paths = compute_dem_features(os.path.join(settings.interim_dir, "dem"))

    # Aggregate per synthetic parcels
    ndvi = np.load(s2_paths["ndvi"])  # HxW
    ndwi = np.load(s2_paths["ndwi"])  # HxW
    vv_vh = np.load(s1_paths["vv_vh"])  # HxW
    h, w = ndvi.shape
    parcel_ids = synthetic_parcel_ids(h, w)
    feats_df = aggregate_to_parcels(parcel_ids, {"ndvi": ndvi, "ndwi": ndwi, "vv_vh": vv_vh})
    features_csv = os.path.join(settings.features_dir, "features.csv")
    save_features(feats_df, features_csv)

    # Train and predict
    model_path = train_or_load(features_csv, settings.models_dir)
    pred_df = predict(model_path, features_csv)
    pred_df = score_water_anomaly(pred_df)
    pred_csv = os.path.join(settings.features_dir, "predictions.csv")
    pred_df.to_csv(pred_csv, index=False)

    # Simple tiles
    # Render simple demo tiles with distinct colormaps and value ranges
    render_cfg = {
        "ndvi": {"arr": ndvi, "cmap": "RdYlGn", "vmin": -0.2, "vmax": 0.8},
        "ndwi": {"arr": ndwi, "cmap": "PuBuGn", "vmin": -0.5, "vmax": 0.5},
    }
    for layer, cfg in render_cfg.items():
        out = os.path.join(settings.tiles_dir, layer, "0", "0", "0.png")
        save_png(cfg["arr"], out, vmin=cfg["vmin"], vmax=cfg["vmax"], colormap=cfg["cmap"])  # type: ignore

    # Summary report tile
    save_blank_tile(os.path.join(settings.tiles_dir, "reports", "summary.png"), text="Summary")

    return {"features": features_csv, "predictions": pred_csv, "model": model_path}
