from __future__ import annotations

import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from ..config import settings
from ..utils.io import ensure_dir
from .routes_maps import router as maps_router
from .routes_reports import router as reports_router
from .routes_bot import router as bot_router
from ..pipeline import run_offline_pipeline


app = FastAPI(title="SatGov MVP")
app.include_router(maps_router)
app.include_router(reports_router)
app.include_router(bot_router)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ingest")
async def ingest(aoi_path: str = Form(...), start: str = Form(...), end: str = Form(...)):
    # Minimal: run offline synthetic pipeline writing tiles and reports
    result = run_offline_pipeline(aoi_path=aoi_path, start=start, end=end)
    return JSONResponse({"status": "ok", **result})


# Serve tiles directory for convenience (static fallback)
tiles_dir = os.path.abspath(settings.tiles_dir)
ensure_dir(tiles_dir)
app.mount("/static/tiles", StaticFiles(directory=tiles_dir), name="tiles")

