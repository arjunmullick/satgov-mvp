from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import geopandas as gpd
from shapely.geometry import mapping
from pystac_client import Client


@dataclass
class STACItem:
    id: str
    assets: Dict[str, str]


def _pick(keys: set[str], candidates: list[str]) -> Optional[str]:
    for c in candidates:
        if c in keys:
            return c
    return None


def search_s2(aoi_geojson_path: str, start: str, end: str, limit: int = 2) -> List[STACItem]:
    gdf = gpd.read_file(aoi_geojson_path).to_crs(4326)
    geom = mapping(gdf.iloc[0].geometry)
    client = Client.open("https://earth-search.aws.element84.com/v1")
    search = client.search(collections=["sentinel-2-l2a"], intersects=geom, datetime=f"{start}/{end}")
    items = []
    for it in list(search.get_items())[:limit]:
        keys = set(it.assets.keys())
        name_map = {
            "blue": _pick(keys, ["B02", "blue", "B2", "coastal" ]),
            "green": _pick(keys, ["B03", "green", "B3" ]),
            "red": _pick(keys, ["B04", "red", "B4" ]),
            "nir": _pick(keys, ["B08", "nir", "B8", "B08_10m", "B8A" ]),
            "scl": _pick(keys, ["SCL", "scl"]),
        }
        assets: Dict[str, str] = {}
        for norm, orig in name_map.items():
            if orig and orig in it.assets:
                assets[norm] = it.assets[orig].href
        items.append(STACItem(id=it.id, assets=assets))
    return items


def search_s1(aoi_geojson_path: str, start: str, end: str, limit: int = 2) -> List[STACItem]:
    gdf = gpd.read_file(aoi_geojson_path).to_crs(4326)
    geom = mapping(gdf.iloc[0].geometry)
    client = Client.open("https://earth-search.aws.element84.com/v1")
    search = client.search(collections=["sentinel-1-grd"], intersects=geom, datetime=f"{start}/{end}")
    items = []
    for it in list(search.get_items())[:limit]:
        assets = {k: v.href for k, v in it.assets.items() if k.lower() in {"vv", "vh"}}
        items.append(STACItem(id=it.id, assets=assets))
    return items
