#!/usr/bin/env python
import argparse
import os
import geopandas as gpd
from src.features.parcel_grid import build_parcel_grid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("aoi", help="Path to AOI GeoJSON/GeoPackage")
    ap.add_argument("out", help="Output GPKG path")
    ap.add_argument("--cell", type=float, default=100.0, help="Cell size meters")
    args = ap.parse_args()
    build_parcel_grid(args.aoi, args.out, cell_size_m=args.cell)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

