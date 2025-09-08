from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any
import geopandas as gpd
from shapely.geometry import mapping
from pystac_client import Client


@dataclass
class STACItem:
    id: str
    assets: Dict[str, str]


def search_s2(aoi_geojson_path: str, start: str, end: str, limit: int = 2) -> List[STACItem]:
    gdf = gpd.read_file(aoi_geojson_path).to_crs(4326)
    geom = mapping(gdf.iloc[0].geometry)
    client = Client.open("https://earth-search.aws.element84.com/v1")
    search = client.search(collections=["sentinel-2-l2a"], intersects=geom, datetime=f"{start}/{end}")
    items = []
    for it in list(search.get_items())[:limit]:
        assets = {k: v.href for k, v in it.assets.items() if k in {"B02", "B03", "B04", "B08", "SCL"}}
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
