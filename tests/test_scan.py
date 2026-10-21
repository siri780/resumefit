from app.scan import connect, remember


def test_remember_returns_only_new_jobs(tmp_path):
    con = connect(tmp_path / "test.db")
    first = remember(con, [{"id": "A:1"}, {"id": "A:2"}])
    second = remember(con, [{"id": "A:2"}, {"id": "A:3"}])
    assert [j["id"] for j in first] == ["A:1", "A:2"]
    assert [j["id"] for j in second] == ["A:3"]