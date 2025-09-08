from __future__ import annotations

import os
from typing import List
import requests

from .stac_search import STACItem
from ..utils.io import ensure_dir


def download_assets(items: List[STACItem], out_dir: str) -> List[str]:
    ensure_dir(out_dir)
    paths: List[str] = []
    for it in items:
        item_dir = os.path.join(out_dir, it.id)
        os.makedirs(item_dir, exist_ok=True)
        for name, href in it.assets.items():
            fname = os.path.join(item_dir, f"{name}.tif")
            try:
                with requests.get(href, stream=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(fname, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                paths.append(fname)
            except Exception:
                # Skip if cannot download
                continue
    return paths
