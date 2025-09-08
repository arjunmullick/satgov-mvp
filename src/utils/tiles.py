from __future__ import annotations

import os
from typing import Sequence, Tuple

import numpy as np
import rasterio
from rasterio.vrt import WarpedVRT
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
import mercantile

from .viz import plt_colormap
from .io import ensure_dir


def tile_bounds_mercator(x: int, y: int, z: int) -> Tuple[float, float, float, float]:
    bbox = mercantile.bounds(x, y, z)
    return bbox.west, bbox.south, bbox.east, bbox.north


def generate_xyz_tiles_from_geotiff(
    raster_path: str,
    layer: str,
    tiles_root: str,
    aoi_bounds_latlon: Sequence[float],
    zooms: Sequence[int],
    cmap: str = "RdYlGn",
    vmin: float | None = None,
    vmax: float | None = None,
    tile_size: int = 256,
) -> None:
    """Generate XYZ tiles for a single-band GeoTIFF. Reprojects on the fly to EPSG:3857.
    aoi_bounds_latlon: (minx, miny, maxx, maxy) in EPSG:4326 for tile coverage enumeration.
    """
    dst_crs = "EPSG:3857"
    cmap_fn = plt_colormap(cmap)
    with rasterio.open(raster_path) as src:
        with WarpedVRT(src, crs=dst_crs, resampling=Resampling.bilinear) as vrt:
            for z in zooms:
                # enumerate tiles covering AOI bbox
                minx, miny, maxx, maxy = aoi_bounds_latlon
                for tile in mercantile.tiles(minx, miny, maxx, maxy, [z]):
                    x, y = tile.x, tile.y
                    west, south, east, north = tile_bounds_mercator(x, y, z)
                    window = from_bounds(west, south, east, north, transform=vrt.transform)
                    out = vrt.read(1, window=window, out_shape=(tile_size, tile_size), resampling=Resampling.bilinear)
                    arr = out.astype(np.float32)
                    if vmin is None:
                        vmin_eff = np.nanpercentile(arr, 2)
                    else:
                        vmin_eff = vmin
                    if vmax is None:
                        vmax_eff = np.nanpercentile(arr, 98)
                    else:
                        vmax_eff = vmax
                    if vmax_eff == vmin_eff:
                        vmax_eff = vmin_eff + 1.0
                    norm = (arr - vmin_eff) / (vmax_eff - vmin_eff)
                    norm = np.clip(norm, 0, 1)
                    rgb = (cmap_fn(norm)[..., :3] * 255).astype(np.uint8)
                    from PIL import Image

                    tile_path = os.path.join(tiles_root, layer, str(z), str(x), f"{y}.png")
                    ensure_dir(os.path.dirname(tile_path))
                    Image.fromarray(rgb).save(tile_path)

