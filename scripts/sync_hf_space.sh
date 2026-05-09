#!/usr/bin/env bash
# Copy DAGIntel app + package into the HF Space git clone for lablab-ai-amd-developer-hackathon.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DST="${ROOT}/hf-space/DAGIntel-airflow-investigator"

if [[ ! -d "$DST/.git" ]]; then
  echo "Expected HF clone at: $DST" >&2
  echo "Clone: git clone https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/DAGIntel-airflow-investigator \"$DST\"" >&2
  exit 1
fi

mkdir -p "$DST/src" "$DST/scenarios"
cp "$ROOT/app.py" "$DST/app.py"
cp "$ROOT/requirements.txt" "$DST/requirements.txt"
rsync -a --delete "$ROOT/src/dagintel/" "$DST/src/dagintel/"
rsync -a --delete "$ROOT/scenarios/" "$DST/scenarios/"
echo "Synced → $DST"
echo "Next: cd \"$DST\" && git add -A && git commit -m \"Sync from monorepo\" && git push"
