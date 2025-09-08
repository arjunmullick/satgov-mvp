from __future__ import annotations

import os
import geopandas as gpd

from ..utils.geoutils import read_aoi, make_square_grid
from ..utils.io import ensure_dir


def build_parcel_grid(aoi_path: str, out_path: str, cell_size_m: float = 100.0) -> str:
    gdf = read_aoi(aoi_path)
    grid = make_square_grid(gdf, cell_size_m=cell_size_m)
    ensure_dir(os.path.dirname(out_path) or ".")
    grid.to_file(out_path, driver="GPKG")
    return out_path

