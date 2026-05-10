from dagintel.scenarios import list_scenarios, load_scenario


def test_list_includes_anchoring():
    rows = list_scenarios()
    assert len(rows) >= 5
    for r in rows:
        assert "id" in r and "title" in r
        assert "anchoring_context" in r
        assert "description" in r


def test_load_matches_list():
    rows = list_scenarios()
    sid = rows[0]["id"]
    full = load_scenario(sid)
    assert full["id"] == sid
    assert "raw_logs" in full
