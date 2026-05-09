import json
from pathlib import Path
SD = Path(__file__).parents[2] / "scenarios"
def list_scenarios():
    return [{"id": p.stem, "title": json.loads(p.read_text())["title"], "anchoring_context": ""} for p in SD.glob("*.json")]
def load_scenario(sid):
    return json.loads((SD / f"{sid}.json").read_text())
