from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from ..config import settings
from ..utils.viz import save_blank_tile


router = APIRouter()


@router.get("/tiles/{layer}/{z}/{x}/{y}.png")
def get_tile(layer: str, z: int, x: int, y: int):
    path = os.path.join(settings.tiles_dir, layer, str(z), str(x), f"{y}.png")
    if not os.path.exists(path):
        # create a blank placeholder tile on demand
        save_blank_tile(path, size=settings.tile_size, text=f"{layer} {z}/{x}/{y}")
    return FileResponse(path, media_type="image/png")


@router.get("/overlay/{layer}")
def get_overlay(layer: str):
    # Provide overlay image URL and AOI bounds for ImageOverlay demo
    img_path = os.path.join(settings.tiles_dir, "overlays", f"{layer}.png")
    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Overlay not found. Run /ingest first.")
    # Read bounds from features/predictions json if present, else use Goa demo bbox
    # For simplicity, use demo AOI bbox
    aoi_path = os.path.join(settings.aoi_dir, "goa_demo.geojson")
    try:
        import geopandas as gpd
        gdf = gpd.read_file(aoi_path).to_crs(4326)
        minx, miny, maxx, maxy = gdf.total_bounds
        bounds = [[miny, minx], [maxy, maxx]]
    except Exception:
        bounds = [[15.30, 73.90], [15.50, 74.10]]
    url = f"/static/tiles/overlays/{layer}.png"
    return JSONResponse({"url": url, "bounds": bounds})
