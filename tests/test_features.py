import numpy as np
from src.features.featurize import aggregate_to_parcels


def test_aggregate_to_parcels_shapes():
    h, w = 16, 16
    parcel_ids = -np.ones((h, w), dtype=int)
    parcel_ids[0:8, 0:8] = 0
    parcel_ids[0:8, 8:16] = 1
    parcel_ids[8:16, 0:16] = 2
    rasters = {
        "ndvi": np.random.rand(h, w).astype("f4"),
        "ndwi": np.random.rand(h, w).astype("f4"),
    }
    df = aggregate_to_parcels(parcel_ids, rasters)
    assert df.shape[0] == 3
    assert any(c.startswith("ndvi_") for c in df.columns)
    assert any(c.startswith("ndwi_") for c in df.columns)

