from dagintel.textutil import serialize_context, truncate_log


def test_serialize_empty():
    assert "infer only from log" in serialize_context({})


def test_serialize_roundtrip():
    s = serialize_context({"dag_id": "d", "task_id": "t"})
    assert "dag_id" in s and "d" in s


def test_truncate_log():
    body, trunc = truncate_log("a" * 50_000, max_total=1000)
    assert trunc and len(body) < 50_000
