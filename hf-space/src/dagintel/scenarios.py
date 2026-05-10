import json
from pathlib import Path
from typing import TypedDict


class ScenarioSummary(TypedDict):
    """List view for UI pickers (`list_scenarios`)."""

    id: str
    title: str
    anchoring_context: str
    description: str


SD = Path(__file__).parents[2] / "scenarios"


def _summary_from_file(path: Path) -> ScenarioSummary:
    data = json.loads(path.read_text(encoding="utf-8"))
    sid = data.get("id", path.stem)
    return {
        "id": sid,
        "title": data.get("title", sid),
        "anchoring_context": (data.get("anchoring_context") or "") if isinstance(data.get("anchoring_context"), str) else "",
        "description": data.get("description", "") if isinstance(data.get("description"), str) else "",
    }


def list_scenarios() -> list[ScenarioSummary]:
    """Stable, JSON-serializable summaries for UI pickers (includes anchoring_context when present)."""
    paths = sorted(SD.glob("*.json"), key=lambda p: p.stem)
    return [_summary_from_file(p) for p in paths]


def load_scenario(sid):
    return json.loads((SD / f"{sid}.json").read_text(encoding="utf-8"))
