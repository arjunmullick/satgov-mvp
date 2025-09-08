from __future__ import annotations

import os
import json
import numpy as np
import geopandas as gpd

from .config import settings
from .utils.io import ensure_dir
from .utils.viz import save_blank_tile, save_png
from .utils.geoutils import read_aoi, bbox_xyxy
from .ingest.preprocess import preprocess_to_interim
from .features.s2_indices import compute_s2_indices
from .features.s1_features import compute_s1_features
from .features.dem_features import compute_dem_features
from .features.featurize import aggregate_to_parcels, save_features
from .models.irrigate_clf import train_or_load, predict
from .models.water_anomaly import score_water_anomaly


def synthetic_parcel_ids(h: int, w: int, n_x: int = 8, n_y: int = 8) -> np.ndarray:
    ids = -np.ones((h, w), dtype=np.int32)
    sx, sy = w // n_x, h // n_y
    pid = 0
    for j in range(n_y):
        for i in range(n_x):
            xs = i * sx
            xe = (i + 1) * sx
            ys = j * sy
            ye = (j + 1) * sy
            ids[ys:ye, xs:xe] = pid
            pid += 1
    return ids


def run_offline_pipeline(aoi_path: str, start: str, end: str) -> dict:
    # Prepare dirs
    ensure_dir(settings.raw_dir)
    ensure_dir(settings.interim_dir)
    ensure_dir(settings.features_dir)
    ensure_dir(settings.models_dir)
    ensure_dir(settings.tiles_dir)

    # Preprocess -> synthetic
    interim_nc = preprocess_to_interim(aoi_path, settings.raw_dir, settings.interim_dir)

    # Indices/features
    s2_paths = compute_s2_indices(interim_nc, os.path.join(settings.interim_dir, "s2"))
    s1_paths = compute_s1_features(os.path.join(settings.interim_dir, "s1"))
    dem_paths = compute_dem_features(os.path.join(settings.interim_dir, "dem"))

    # Aggregate per synthetic parcels
    ndvi = np.load(s2_paths["ndvi"])  # HxW
    ndwi = np.load(s2_paths["ndwi"])  # HxW
    vv_vh = np.load(s1_paths["vv_vh"])  # HxW
    h, w = ndvi.shape
    parcel_ids = synthetic_parcel_ids(h, w)
    feats_df = aggregate_to_parcels(parcel_ids, {"ndvi": ndvi, "ndwi": ndwi, "vv_vh": vv_vh})
    features_csv = os.path.join(settings.features_dir, "features.csv")
    save_features(feats_df, features_csv)

    # Train and predict
    model_path = train_or_load(features_csv, settings.models_dir)
    pred_df = predict(model_path, features_csv)
    pred_df = score_water_anomaly(pred_df)
    pred_csv = os.path.join(settings.features_dir, "predictions.csv")
    pred_df.to_csv(pred_csv, index=False)

    # Simple tiles
    # Render simple demo tiles with distinct colormaps and value ranges
    render_cfg = {
        "ndvi": {"arr": ndvi, "cmap": "RdYlGn", "vmin": -0.2, "vmax": 0.8},
        "ndwi": {"arr": ndwi, "cmap": "PuBuGn", "vmin": -0.5, "vmax": 0.5},
    }
    for layer, cfg in render_cfg.items():
        out = os.path.join(settings.tiles_dir, layer, "0", "0", "0.png")
        save_png(cfg["arr"], out, vmin=cfg["vmin"], vmax=cfg["vmax"], colormap=cfg["cmap"])  # type: ignore

    # AOI-cropped overlay images for ImageOverlay demo
    aoi_gdf = read_aoi(aoi_path)
    minx, miny, maxx, maxy = bbox_xyxy(aoi_gdf)
    overlays_dir = os.path.join(settings.tiles_dir, "overlays")
    os.makedirs(overlays_dir, exist_ok=True)
    save_png(ndvi, os.path.join(overlays_dir, "ndvi.png"), vmin=-0.2, vmax=0.8, colormap="RdYlGn")
    save_png(ndwi, os.path.join(overlays_dir, "ndwi.png"), vmin=-0.5, vmax=0.5, colormap="PuBuGn")

    # Summary report tile
    save_blank_tile(os.path.join(settings.tiles_dir, "reports", "summary.png"), text="Summary")

    return {
        "features": features_csv,
        "predictions": pred_csv,
        "model": model_path,
        "overlay_bounds": [[miny, minx], [maxy, maxx]],
    }


def run_stac_pipeline(aoi_path: str, start: str, end: str, limit: int = 2, zooms: list[int] | None = None) -> dict:
    """Search STAC for S2, compute NDVI/NDWI, write GeoTIFFs, and generate XYZ tiles."""
    ensure_dir(settings.raw_dir)
    ensure_dir(settings.interim_dir)
    ensure_dir(settings.tiles_dir)

    zooms = zooms or [8, 9, 10, 11, 12]

    try:
        import geopandas as gpd
        from shapely.geometry import mapping
        from pystac_client import Client
        import stackstac
        import rioxarray  # noqa: F401

        aoi = gpd.read_file(aoi_path).to_crs(4326)
        minx, miny, maxx, maxy = aoi.total_bounds
        geom = mapping(aoi.iloc[0].geometry)
        client = Client.open("https://earth-search.aws.element84.com/v1")
        search = client.search(collections=["sentinel-2-l2a"], intersects=geom, datetime=f"{start}/{end}")
        s2_items = list(search.get_items())[:limit]
        if not s2_items:
            return {"status": "no_items", "message": "No S2 items from STAC search."}
        # Let stackstac pick bounds; then clip to AOI bbox to avoid bounds issues
        # Try common asset key sets for S2
        assets_try = [["B02", "B03", "B04", "B08"], ["blue", "green", "red", "nir"]]
        last_err = None
        stack = None
        for aset in assets_try:
            try:
                stack = stackstac.stack(s2_items, assets=aset)  # time, band, y, x
                break
            except Exception as ee:
                last_err = ee
                continue
        if stack is None:
            raise last_err or Exception("Failed to stack S2 assets")
        comp = stack.median(dim="time")
        try:
            comp = comp.rio.reproject("EPSG:4326")
        except Exception:
            pass
        comp = comp.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
        blue = comp.sel(band="B02").astype("float32") / 10000.0
        green = comp.sel(band="B03").astype("float32") / 10000.0
        red = comp.sel(band="B04").astype("float32") / 10000.0
        nir = comp.sel(band="B08").astype("float32") / 10000.0
        ndvi = (nir - red) / ((nir + red).where((nir + red) != 0, 1))
        ndwi = (green - nir) / ((green + nir).where((green + nir) != 0, 1))
        ndvi = ndvi.rio.write_crs(4326)
        ndwi = ndwi.rio.write_crs(4326)
        ndvi_path = os.path.join(settings.interim_dir, "ndvi.tif")
        ndwi_path = os.path.join(settings.interim_dir, "ndwi.tif")
        ndvi.rio.to_raster(ndvi_path, compress="deflate")
        ndwi.rio.to_raster(ndwi_path, compress="deflate")

        from .utils.tiles import generate_xyz_tiles_from_geotiff
        generate_xyz_tiles_from_geotiff(ndvi_path, "ndvi", settings.tiles_dir, aoi.total_bounds, zooms, cmap="RdYlGn", vmin=-0.2, vmax=0.8)
        generate_xyz_tiles_from_geotiff(ndwi_path, "ndwi", settings.tiles_dir, aoi.total_bounds, zooms, cmap="PuBuGn", vmin=-0.5, vmax=0.5)

        # Sentinel-1 GRD VV/VH composites and ratio
        try:
            s1_search = client.search(collections=["sentinel-1-grd"], intersects=geom, datetime=f"{start}/{end}")
            s1_items = list(s1_search.get_items())[:limit]
            if s1_items:
                s1_stack = stackstac.stack(s1_items, assets=["VV", "VH"])  # time, band, y, x
                s1_comp = s1_stack.median(dim="time")
                try:
                    s1_comp = s1_comp.rio.reproject("EPSG:4326")
                except Exception:
                    pass
                s1_comp = s1_comp.rio.clip_box(minx=minx, miny=miny, maxx=maxx, maxy=maxy)
                vv = (10.0 * (s1_comp.sel(band="VV").astype("float32"))).rio.write_crs(4326)
                vh = (10.0 * (s1_comp.sel(band="VH").astype("float32"))).rio.write_crs(4326)
                # Ratio in linear units approximated by exp(dB/10); here keep in dB diff as proxy
                ratio = (vv - vh).rio.write_crs(4326)
                vv_path = os.path.join(settings.interim_dir, "s1_vv.tif")
                vh_path = os.path.join(settings.interim_dir, "s1_vh.tif")
                ratio_path = os.path.join(settings.interim_dir, "s1_ratio.tif")
                vv.rio.to_raster(vv_path, compress="deflate")
                vh.rio.to_raster(vh_path, compress="deflate")
                ratio.rio.to_raster(ratio_path, compress="deflate")

                generate_xyz_tiles_from_geotiff(vv_path, "s1_vv", settings.tiles_dir, aoi.total_bounds, zooms, cmap="Greys", vmin=-25, vmax=0)
                generate_xyz_tiles_from_geotiff(vh_path, "s1_vh", settings.tiles_dir, aoi.total_bounds, zooms, cmap="Greys", vmin=-30, vmax=-5)
                generate_xyz_tiles_from_geotiff(ratio_path, "s1_ratio", settings.tiles_dir, aoi.total_bounds, zooms, cmap="Magma", vmin=0, vmax=15)
        except Exception:
            pass

        return {"status": "ok", "ndvi": ndvi_path, "ndwi": ndwi_path}
    except Exception as e:
        # Fallback: use first S2 item assets directly via rasterio to build a single-scene composite
        try:
            from .ingest.stac_search import search_s2
            import geopandas as gpd
            import rasterio
            from rasterio.transform import from_bounds
            from rasterio.warp import reproject, Resampling
            import numpy as np

            aoi = gpd.read_file(aoi_path).to_crs(4326)
            minx, miny, maxx, maxy = aoi.total_bounds
            items = search_s2(aoi_path, start, end, limit=5)
            if not items:
                return {"status": "error", "message": str(e)}
            # Pick first item that has normalized bands
            chosen = None
            for it in items:
                a = it.assets
                if all(k in a for k in ("blue", "green", "red", "nir")):
                    chosen = a
                    break
            if chosen is None:
                return {"status": "error", "message": "S2 item missing required bands"}
            # Target grid in EPSG:4326 at ~0.00009 deg (~10 m)
            res = 0.00009
            width = max(1, int(np.ceil((maxx - minx) / res)))
            height = max(1, int(np.ceil((maxy - miny) / res)))
            dst_transform = from_bounds(minx, miny, maxx, maxy, width, height)
            dst_crs = "EPSG:4326"

            def reproject_band(href: str) -> np.ndarray:
                dst = np.zeros((height, width), dtype=np.float32)
                with rasterio.open(href) as src:
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=dst,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=dst_transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.bilinear,
                    )
                return dst

            blue = reproject_band(chosen["blue"]) / 10000.0
            green = reproject_band(chosen["green"]) / 10000.0
            red = reproject_band(chosen["red"]) / 10000.0
            nir = reproject_band(chosen["nir"]) / 10000.0
            ndvi = (nir - red) / np.where((nir + red) != 0, (nir + red), 1)
            ndwi = (green - nir) / np.where((green + nir) != 0, (green + nir), 1)

            # Write GeoTIFFs
            profile = {
                "driver": "GTiff",
                "height": height,
                "width": width,
                "count": 1,
                "dtype": "float32",
                "crs": dst_crs,
                "transform": dst_transform,
                "compress": "deflate",
            }
            ndvi_path = os.path.join(settings.interim_dir, "ndvi.tif")
            ndwi_path = os.path.join(settings.interim_dir, "ndwi.tif")
            with rasterio.open(ndvi_path, "w", **profile) as dst:
                dst.write(ndvi.astype(np.float32), 1)
            with rasterio.open(ndwi_path, "w", **profile) as dst:
                dst.write(ndwi.astype(np.float32), 1)

            # Tiles
            generate_xyz_tiles_from_geotiff(ndvi_path, "ndvi", settings.tiles_dir, (minx, miny, maxx, maxy), zooms, cmap="RdYlGn", vmin=-0.2, vmax=0.8)
            generate_xyz_tiles_from_geotiff(ndwi_path, "ndwi", settings.tiles_dir, (minx, miny, maxx, maxy), zooms, cmap="PuBuGn", vmin=-0.5, vmax=0.5)
            return {"status": "ok", "ndvi": ndvi_path, "ndwi": ndwi_path, "fallback": True}
        except Exception as e2:
            return {"status": "error", "message": str(e2)}
