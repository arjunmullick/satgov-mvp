SatGov MVP: Satellite Vision for Irrigation and Water Health

Overview
- Local, offline-first prototype for Goa to ingest satellite imagery (STAC or local GeoTIFFs), compute vegetation/water indices, train simple models, and serve tiled maps and PNG reports via FastAPI with a minimal Leaflet UI.
- MVPs: (A) Crop/irrigation readiness, (B) Aquaculture pond stress, (C) River/lake pollution hotspots.

Stack & Constraints
- Language: Python 3.11 (Conda env)
- Core libs: rasterio, rio-cogeo, numpy, xarray, pandas, geopandas, shapely, pyproj, pystac-client, stackstac, rioxarray, opencv-python, scikit-learn, xgboost, torch (CPU), fastapi, uvicorn, jinja2, python-multipart, Pillow, matplotlib, folium/Leaflet.
- Data: Sentinel-2 L2A, Sentinel-1 GRD, Landsat 8/9, DEM (SRTM/ALOS) via STAC or local files. No cloud creds required.
- Offline-first: Works locally with a small AOI; downloads optional (not enabled by default).

Repository Structure
```
satgov-mvp/
  README.md
  .env.example
  environment.yml
  data/
    aoi/           # user AOI GeoJSON or shapefiles
    raw/           # downloaded rasters
    interim/       # reprojected/clipped
    features/      # per-parcel features
    labels/        # optional labels
    models/        # saved models
    tiles/         # web tiles / PNG exports
  notebooks/
    00_explore.ipynb
    10_feature_checks.ipynb
  src/
    config.py
    utils/ (io, geoutils, indices, viz)
    ingest/ (stac_search, download, preprocess)
    features/ (parcel_grid, s2_indices, s1_features, landsat_lst, dem_features, featurize)
    models/ (irrigate_clf, water_anomaly, unet_seg)
    api/ (server, routes_maps, routes_reports, routes_bot)
    pipeline.py
  web/
    leaflet.html
  tests/
    test_indices.py, test_features.py, test_api.py
  scripts/
    make_aoi_grid.py, run_pipeline.sh
```

Environment Setup
- Create and activate env:
  - `conda env create -f environment.yml`
  - `conda activate satgov`
- Optional: copy `.env.example` to `.env` and adjust variables.

Pip/Venv Fallback (no Conda)
- Prerequisites (macOS via Homebrew):
  - `brew install python` (3.11+)
  - Optional but recommended: `brew install gdal` (not strictly required for prebuilt wheels)
- Create venv and install:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate` (or `source .venv/bin/activate.fish`)
  - `pip install --upgrade pip setuptools wheel`
  - `pip install -r requirements.txt`
- Run server:
  - `uvicorn src.api.server:app --reload`
- If you hit binary wheel issues (rare on macOS/Linux):
  - Ensure you are on Python 3.11
  - Upgrade pip: `pip install --upgrade pip`
  - Try reinstalling specific libs: `pip install --no-binary=:all: shapely pyproj` (only if needed)

Quick Start
- Start API server (in repo root):
  - `uvicorn src.api.server:app --reload`
- Open web UI:
  - Open `web/leaflet.html` in a browser (expects server at `http://localhost:8000`).
- Run end-to-end pipeline (synthetic offline fallback):
  - `bash scripts/run_pipeline.sh --aoi data/aoi/goa_demo.geojson --start 2024-11-01 --end 2025-03-31`

Step-by-Step: Test, Run, and Demo
1) Prerequisites
   - macOS/Linux with Python 3.11+
   - Option A (recommended): Conda/Miniforge
   - Option B: Pip + venv

2) Setup
   - Conda:
     - `cd satgov-mvp`
     - `conda env create -f environment.yml`
     - `conda activate satgov`
   - OR Pip/venv:
     - `cd satgov-mvp`
     - `python3 -m venv .venv`
     - `source .venv/bin/activate`
     - `pip install --upgrade pip setuptools wheel`
     - `pip install -r requirements.txt`

3) Generate Demo Data (synthetic, offline)
   - Ensure sample AOI exists: `data/aoi/goa_demo.geojson` (provided).
   - Run pipeline:
     - `bash scripts/run_pipeline.sh --aoi data/aoi/goa_demo.geojson --start 2024-11-01 --end 2025-03-31`
   - Check outputs:
     - `ls data/features/` (features.csv, predictions.csv)
     - `ls data/models/` (irrigate_clf.pkl)
     - `ls data/tiles/` (ndvi/…, ndwi/…, reports/…)

4) Run API Server and Web UI
   - From repo root: `uvicorn src.api.server:app --reload`
   - Open: `http://localhost:8000/` → auto-redirects to `/web/leaflet.html`
   - Use panel buttons to toggle NDVI/NDWI overlays (tiles are served at `/tiles/...`).

5) API Smoke Tests (curl)
   - Health: `curl -s localhost:8000/health`
   - Ingest (re-run pipeline):
     - `curl -s -X POST localhost:8000/ingest -F aoi_path=data/aoi/goa_demo.geojson -F start=2024-11-01 -F end=2025-03-31 | jq`
   - Tiles (autocreate if missing):
     - `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/tiles/ndvi/0/0/0.png`
   - Parcel report (mock): `curl -s localhost:8000/report/parcel/1 | jq`
   - Village report (mock): `curl -s localhost:8000/report/village/Assagao | jq`
   - WhatsApp-style bot:
     - `curl -s -X POST localhost:8000/bot -F text="1" | jq`
     - `curl -s -X POST localhost:8000/bot -F text="Assagao" | jq`

6) Inspect Model/Features
   - Print predictions head:
```
python - <<'PY'
import pandas as pd; print(pd.read_csv("data/features/predictions.csv").head())
PY
```

7) Optional: Make Parcel Grid
   - Build a 100 m parcel grid GeoPackage:
     - `python scripts/make_aoi_grid.py data/aoi/goa_demo.geojson data/interim/parcel_grid.gpkg --cell 100`

8) Run Tests
   - Install pytest if not present: `pip install pytest`
   - Run: `pytest -q`
   - Covered: indices shapes/ranges, parcel aggregation, API endpoints.

Troubleshooting
- `conda: command not found`: install Miniforge (`brew install --cask miniforge`; `conda init zsh`; restart shell) or use Pip/Venv flow.
- 404 at `/`: ensure the server is the latest (root redirects to `/web/leaflet.html`).
- Port in use: `uvicorn src.api.server:app --reload --port 8001`.
- Pip/venv binary wheels issue: ensure Python 3.11; `pip install --upgrade pip`; consider `brew install gdal` or switch to Conda.

Endpoints
- `GET /health` → `{"ok": true}`
- `POST /ingest` (form-data `aoi_path`, `start`, `end`) → runs pipeline (offline synthetic by default); returns paths to outputs.
- `GET /tiles/{layer}/{z}/{x}/{y}.png` → serve tiles from `data/tiles/{layer}/…` (auto-creates placeholders if missing).
- `GET /report/parcel/{id}` → returns PNG path + JSON metrics for a parcel (mocked offline).
- `GET /report/village/{name}` → returns village summary PNG + CSV link (mocked offline).
- `POST /bot` (form `text:"<village or parcel id>"`) → returns a small JSON with links to reports.

Sample curl
- `curl -s localhost:8000/health`
- `curl -s -X POST localhost:8000/ingest -F aoi_path=data/aoi/goa_demo.geojson -F start=2024-11-01 -F end=2025-03-31 | jq` 
- `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/tiles/ndvi/0/0/0.png`

Minimal User Flow
1) Place an AOI GeoJSON at `data/aoi/goa_demo.geojson` (~20×20 km polygon in EPSG:4326).
2) Run the pipeline: `bash scripts/run_pipeline.sh --aoi data/aoi/goa_demo.geojson --start 2024-11-01 --end 2025-03-31`.
3) Start the server: `uvicorn src.api.server:app --reload`.
4) Open `web/leaflet.html` and toggle overlays; click parcels (mock) and fetch reports.

Pipeline (Current Offline Implementation)
- Ingest/Preprocess: `src/ingest/preprocess.py` creates a synthetic Sentinel-2-like scene and saves to NetCDF under `data/interim/`.
- Indices & Features: `src/features/s2_indices.py` computes NDVI/EVI/NDWI/MNDWI arrays (synthetic SWIR), `s1_features.py` creates VV/VH/ratio, `dem_features.py` adds slope/aspect.
- Parcel Fabric: Synthetic parcel IDs grid; `src/features/featurize.py` aggregates per-parcel stats (p50/p90/mean/std) and writes CSV.
- Models: `src/models/irrigate_clf.py` trains GradientBoosting with weak labels fallback; `src/models/water_anomaly.py` adds MNDWI z-score flags.
- Exports: Writes a base XYZ tile `data/tiles/ndvi/0/0/0.png` (and NDWI); generates simple placeholder report PNGs and action CSV stub.

Moving to Real Data (Next Steps)
- STAC Search & Download (`src/ingest/stac_search.py`, `download.py`):
  - Implemented with `pystac-client` against Element84 STAC; stacked via `stackstac`.
  - Sentinel-2 L2A: B02, B03, B04, B08 for NDVI/NDWI composites; Sentinel-1 GRD: VV/VH and VV–VH ratio.
- Preprocess (`src/ingest/preprocess.py`):
  - Reproject to UTM for computation; clip to AOI.
  - S2 cloud/shadow mask using SCL (classes 3, 8, 9, 10, 11).
  - S1 speckle reduction: multi-date median composite or simple Lee filter.
- Features (`src/features/*`):
  - Replace synthetic arrays with real rasters via rioxarray/xarray; add S1 GLCM textures (contrast, homogeneity).
  - DEM slope/aspect from SRTM/ALOS; optional flow accumulation proxy.
  - Temporal stats per parcel (p10/p50/p90, range, std, simple trends).
- Tiles & Reports:
  - Generate XYZ tiles via rio-tiler/titiler or COGs (rio-cogeo); add multiple zooms.
  - Build matplotlib PNG summaries with NDVI/NDWI charts, classification pie, and top-N action list CSVs.
- Web UI:
  - Add AOI upload form to call `POST /ingest`; parcel click popups to fetch `/report/parcel/{id}`.
  - Added buttons: NDVI/NDWI (tiles), NDVI/NDWI Overlay (ImageOverlay demo), and S1 VV/VH/Ratio.

Using Local GeoTIFFs Instead of STAC
- Place your COG/GeoTIFF assets under `data/raw/` and adjust `src/ingest/preprocess.py` to read from there before attempting STAC.
- Keep rasters in a consistent CRS (will be reprojected to UTM internally) and clipped to AOI for performance.

Scripts
- `scripts/run_pipeline.sh`: validates AOI, runs the offline pipeline, writes features/tiles/reports.
- `scripts/make_aoi_grid.py`: builds a 100 m parcel grid GeoPackage from a given AOI.

Testing
- Run tests locally (offline, fast):
  - `pytest -q`
- Covered:
  - Indices numerical shapes/ranges (`tests/test_indices.py`)
  - Parcel aggregation schema (`tests/test_features.py`)
  - API health, tile creation, and mock report (`tests/test_api.py`)

Data Layout
- `data/aoi/`           user AOI GeoJSON/shapefiles
- `data/raw/`           downloaded rasters
- `data/interim/`       reprojected/clipped/intermediate
- `data/features/`      per-parcel features and predictions CSVs
- `data/labels/`        optional labels (e.g., irrigation_labels.csv)
- `data/models/`        saved models (.pkl/.pt)
- `data/tiles/`         web tiles / PNG reports

Environment Variables
- Copy `.env.example` to `.env` to override defaults:
  - `DATA_DIR` (default `data`)
  - `LOG_LEVEL` (default `INFO`)
  - `TILE_SIZE` (default `256`)

Acceptance Targets
- End-to-end for a small AOI (≤100 km²) in ≤10 minutes on a laptop (excluding downloads).
- Leaflet page shows at least NDVI and NDWI layers and parcel/village mock reports.
- `/bot` returns a PNG & CSV link for a known key.

Roadmap / TODOs
- Hook up real STAC search/download and caching.
- Implement S2 SCL cloud/shadow mask; S1 speckle reduction and textures.
- Add DEM slope/aspect and optional rainfall/time-trend features.
- Generate multi-zoom XYZ tiles via rio-tiler or COG pathway.
- Enrich reports and web UI with charts and interactions.
Metric Cheat Sheet (What NDVI/NDWI mean)
- NDVI (Normalized Difference Vegetation Index): `(NIR - Red) / (NIR + Red)` — healthy vegetation ~0.5–0.8; barren/built-up/water <0.2.
- EVI (Enhanced Vegetation Index): vegetation index robust to canopy background; uses Blue band and coefficients.
- NDWI (Normalized Difference Water Index): `(Green - NIR) / (Green + NIR)` — highlights surface water/wetness (higher = wetter).
- MNDWI (Modified NDWI): `(Green - SWIR1) / (Green + SWIR1)` — sharper water delineation in presence of built-up.
- S1 VV/VH (backscatter, dB): microwave returns sensitive to roughness/moisture; `VV-VH` (dB) is a simple ratio proxy.

Real STAC Ingest (Detailed)
1) Start server: `uvicorn src.api.server:app --reload`
2) Trigger ingest:
   - `curl -s -X POST 'http://localhost:8000/ingest' \
      -F 'aoi_path=data/aoi/goa_demo.geojson' \
      -F 'start=2024-11-01' -F 'end=2025-03-31' \
      -F 'source=stac' | jq`
3) Output:
   - GeoTIFFs in `data/interim/ndvi.tif`, `data/interim/ndwi.tif` (and `s1_*.tif` if available)
   - XYZ tiles in `data/tiles/ndvi`, `data/tiles/ndwi`, `data/tiles/s1_vv`, `data/tiles/s1_vh`, `data/tiles/s1_ratio`
4) View:
   - Open `http://localhost:8000/` and toggle NDVI/NDWI and S1 layer buttons.
5) Notes:
   - Keep AOI/date modest for speed; adjust `limit` and `zooms` in `run_stac_pipeline` if needed.
