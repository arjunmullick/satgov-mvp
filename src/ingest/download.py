from __future__ import annotations

import os
from typing import List

from .stac_search import STACItem
from ..utils.io import ensure_dir


def download_assets(items: List[STACItem], out_dir: str) -> List[str]:
    ensure_dir(out_dir)
    # TODO: Download assets to out_dir; for now return empty (offline)
    return []

