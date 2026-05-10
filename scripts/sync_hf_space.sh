#!/usr/bin/env bash
# Copy DAGIntel app + package into the HF Space git clone for lablab-ai-amd-developer-hackathon.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DST="${ROOT}/hf-space/DAGIntel-airflow-investigator"

DRY_RUN=0
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=1
  fi
done

if [[ ! -d "$DST/.git" ]]; then
  echo "Expected HF clone at: $DST" >&2
  echo "Clone: git clone https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/DAGIntel-airflow-investigator \"$DST\"" >&2
  exit 1
fi

rsync_copy() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] rsync $*"
    rsync -an "$@"
  else
    rsync -a "$@"
  fi
}

mkdir -p "$DST/src" "$DST/scenarios"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] cp app.py requirements README pyproject → $DST"
else
  cp "$ROOT/app.py" "$DST/app.py"
  cp "$ROOT/requirements.txt" "$DST/requirements.txt"
  cp "$ROOT/hf-space/README.md" "$DST/README.md"
  if [[ -f "$ROOT/pyproject.toml" ]]; then
    cp "$ROOT/pyproject.toml" "$DST/pyproject.toml"
  fi
  if [[ -f "$ROOT/.gitattributes" ]]; then
    cp "$ROOT/.gitattributes" "$DST/.gitattributes"
  fi
fi
rsync_copy --delete "$ROOT/src/dagintel/" "$DST/src/dagintel/"
rsync_copy --delete "$ROOT/scenarios/" "$DST/scenarios/"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] no files written."
else
  echo "Synced → $DST"
  echo "Next: cd \"$DST\" && git add -A && git commit -m \"Sync from monorepo\" && git push"
fi
