from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class STACItem:
    id: str
    assets: Dict[str, str]


def search_s2(aoi_geojson_path: str, start: str, end: str, limit: int = 2) -> List[STACItem]:
    # TODO: Implement real STAC search via pystac-client
    # Offline fallback returns empty list
    return []


def search_s1(aoi_geojson_path: str, start: str, end: str, limit: int = 2) -> List[STACItem]:
    # TODO: Implement real STAC search via pystac-client
    return []

