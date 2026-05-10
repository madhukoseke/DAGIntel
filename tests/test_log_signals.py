import json

from dagintel.tools.log_signals import ExtractAirflowLogSignalsTool, extract_airflow_log_signals_dict


_SAMPLE = """\
[2026-05-09T06:00:00.001+0000] {taskinstance.py:3313} ERROR - Task failed
airflow.exceptions.AirflowSensorTimeout: Sensor has timed out\n
[2026-05-09T07:30:00.200+0000] INFO - dag_id=mart_daily_dag, task_id=wait_upstream try 2/3 scheduled__2026-05-09T05:00:00+00:00\n
"""


def test_extract_dict_finds_airflow_ids():
    data = extract_airflow_log_signals_dict(_SAMPLE)
    p = data["patterns"]
    assert "mart_daily_dag" in p.get("dag_ids", [])
    assert "wait_upstream" in p["task_ids"]
    assert any("scheduled__" in r for r in p.get("run_ids", []))
    assert "AirflowSensorTimeout" in "".join(p.get("airflow_exceptions", []))
    assert len(data["snippet_timestamps"]) >= 1


def test_tool_returns_json_roundtrip():
    tool = ExtractAirflowLogSignalsTool()
    js = tool._run(_SAMPLE)
    obj = json.loads(js)
    assert obj["_truncated_input"] is False
    assert "patterns" in obj


def test_empty_log():
    d = extract_airflow_log_signals_dict("")
    assert d["patterns"] == {}
