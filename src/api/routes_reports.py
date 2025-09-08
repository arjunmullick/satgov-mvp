from __future__ import annotations

import os
import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse

from ..config import settings
from ..utils.viz import save_blank_tile


router = APIRouter()


@router.get("/report/parcel/{pid}")
def report_parcel(pid: int):
    # Mock report: return a PNG path and dummy metrics
    img_path = os.path.join(settings.tiles_dir, "reports", f"parcel_{pid}.png")
    if not os.path.exists(img_path):
        save_blank_tile(img_path, text=f"Parcel {pid}")
    payload = {"png": img_path, "metrics": {"id": pid, "ndvi": 0.5, "ndwi": 0.1}}
    return JSONResponse(payload)


@router.get("/report/village/{name}")
def report_village(name: str):
    img_path = os.path.join(settings.tiles_dir, "reports", f"village_{name}.png")
    csv_path = os.path.join(settings.features_dir, f"actions_{name}.csv")
    if not os.path.exists(img_path):
        save_blank_tile(img_path, text=f"Village {name}")
    if not os.path.exists(csv_path):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w") as f:
            f.write("id,lat,lon,type,score,reason,date\n")
    return JSONResponse({"png": img_path, "csv": csv_path})

