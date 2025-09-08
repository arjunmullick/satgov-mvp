from __future__ import annotations

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse


router = APIRouter()


@router.post("/bot")
async def bot(text: str = Form("")):
    # Echo-style stub: interpret text as village or parcel id
    t = text.strip()
    info = {}
    if t.isdigit():
        info = {"type": "parcel", "id": int(t), "report": f"/report/parcel/{t}"}
    else:
        info = {"type": "village", "name": t, "report": f"/report/village/{t}"}
    return JSONResponse({"ok": True, **info})

