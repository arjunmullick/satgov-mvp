from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

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

