from __future__ import annotations

from typing import Tuple

import geopandas as gpd
from shapely.geometry import Polygon, shape, mapping
from shapely.ops import unary_union
from pyproj import CRS


def read_aoi(aoi_path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(aoi_path)
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    return gdf


def get_utm_crs_for_gdf(gdf: gpd.GeoDataFrame) -> CRS:
    centroid = gdf.to_crs(4326).unary_union.centroid
    lon, lat = centroid.x, centroid.y
    utm = CRS.from_user_input(f"+proj=utm +zone={(int((lon + 180) / 6) % 60) + 1} +datum=WGS84 +units=m +no_defs")
    if lat < 0:
        utm = CRS.from_dict({**utm.to_dict(), "south": True})
    return utm


def dissolve_aoi(gdf: gpd.GeoDataFrame) -> gpd.GeoSeries:
    geom = unary_union(gdf.geometry)
    return gpd.GeoSeries([geom], crs=gdf.crs)


def bbox_xyxy(gdf: gpd.GeoDataFrame) -> Tuple[float, float, float, float]:
    minx, miny, maxx, maxy = gdf.total_bounds
    return minx, miny, maxx, maxy


def make_square_grid(aoi: gpd.GeoDataFrame, cell_size_m: float = 100.0) -> gpd.GeoDataFrame:
    utm = get_utm_crs_for_gdf(aoi)
    aoi_utm = aoi.to_crs(utm)
    minx, miny, maxx, maxy = aoi_utm.total_bounds
    polys = []
    i = 0
    y = miny
    while y < maxy:
        x = minx
        while x < maxx:
            poly = Polygon([(x, y), (x + cell_size_m, y), (x + cell_size_m, y + cell_size_m), (x, y + cell_size_m)])
            if poly.intersects(aoi_utm.unary_union):
                polys.append(poly)
            x += cell_size_m
            i += 1
        y += cell_size_m
    grid = gpd.GeoDataFrame({"id": list(range(len(polys)))}, geometry=polys, crs=utm)
    return grid.to_crs(aoi.crs)

