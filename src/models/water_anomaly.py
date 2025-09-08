from __future__ import annotations

import numpy as np
import pandas as pd


def zscore(series: pd.Series) -> pd.Series:
    mu = series.mean()
    sd = series.std(ddof=0) or 1.0
    return (series - mu) / sd


def score_water_anomaly(features_df: pd.DataFrame) -> pd.DataFrame:
    df = features_df.copy()
    if "mndwi_mean" in df.columns:
        df["water_anom"] = zscore(df["mndwi_mean"]).abs()
    else:
        df["water_anom"] = 0.0
    df["water_flag"] = df["water_anom"] > 1.5
    return df

