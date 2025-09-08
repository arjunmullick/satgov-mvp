from __future__ import annotations

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from ..utils.io import ensure_dir


FEATURES = [
    "ndvi_p50", "ndvi_p90", "ndvi_mean", "ndvi_std",
    "ndwi_p50", "ndwi_p90", "ndwi_mean", "ndwi_std",
    "vv_vh_p50", "vv_vh_p90", "vv_vh_mean", "vv_vh_std",
]


def weak_labels(df: pd.DataFrame) -> pd.Series:
    # Simple rule-based labels: irrigated, rainfed, fallow
    irrigated = (df.get("ndvi_p50", 0) > 0.45) & (df.get("ndwi_p50", 0) > 0.1)
    fallow = (df.get("ndvi_p90", 0) < 0.2)
    labels = np.where(irrigated, "irrigated", np.where(fallow, "fallow", "rainfed"))
    return pd.Series(labels, index=df.index)


def train_or_load(features_csv: str, model_dir: str) -> str:
    ensure_dir(model_dir)
    model_path = os.path.join(model_dir, "irrigate_clf.pkl")
    if os.path.exists(model_path):
        return model_path
    df = pd.read_csv(features_csv)
    if "label" not in df.columns:
        df["label"] = weak_labels(df)
    X = df.reindex(columns=FEATURES).fillna(0.0).values
    y = df["label"].values
    if len(np.unique(y)) < 2:
        y = np.where(df["ndvi_p50"] > df["ndvi_p50"].median(), "irrigated", "rainfed")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    clf = GradientBoostingClassifier(random_state=42)
    clf.fit(X_train, y_train)
    _ = classification_report(y_test, clf.predict(X_test), output_dict=True)
    joblib.dump({"model": clf, "features": FEATURES}, model_path)
    return model_path


def predict(model_path: str, features_csv: str) -> pd.DataFrame:
    obj = joblib.load(model_path)
    clf = obj["model"]
    features = obj["features"]
    df = pd.read_csv(features_csv)
    X = df.reindex(columns=features).fillna(0.0).values
    probs = clf.predict_proba(X)
    classes = clf.classes_
    for i, c in enumerate(classes):
        df[f"prob_{c}"] = probs[:, i]
    return df

