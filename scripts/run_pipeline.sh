#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --aoi <path> --start <YYYY-MM-DD> --end <YYYY-MM-DD>" >&2
}

AOI=""
START=""
END=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --aoi) AOI="$2"; shift 2;;
    --start) START="$2"; shift 2;;
    --end) END="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "$AOI" || -z "$START" || -z "$END" ]]; then
  usage; exit 1
fi

if [[ ! -f "$AOI" ]]; then
  echo "AOI file not found: $AOI" >&2
  exit 1
fi

export PYTHONPATH=$(cd "$(dirname "$0")/.." && pwd)
python3 - "$AOI" "$START" "$END" <<'PY'
import os, sys
from src.pipeline import run_offline_pipeline

aoi = os.environ.get('AOI_PATH') or sys.argv[1]
start = os.environ.get('START_DATE') or sys.argv[2]
end = os.environ.get('END_DATE') or sys.argv[3]
res = run_offline_pipeline(aoi, start, end)
print(res)
PY

echo "Pipeline completed. See data/features and data/tiles."
