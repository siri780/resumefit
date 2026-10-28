from app.scan import connect, remember


def test_remember_returns_only_new_jobs(tmp_path):
    con = connect(tmp_path / "test.db")
    first = remember(con, [{"id": "A:1"}, {"id": "A:2"}])
    second = remember(con, [{"id": "A:2"}, {"id": "A:3"}])
    assert [j["id"] for j in first] == ["A:1", "A:2"]
    assert [j["id"] for j in second] == ["A:3"]

def test_new_company_is_seeded_silently(tmp_path):
    con = connect(tmp_path / "test.db")
    remember(con, [{"id": "A:1", "company": "A"}])
    new = remember(con, [{"id": "A:2", "company": "A"}, {"id": "Amazon:9", "company": "Amazon"}])
    assert [j["id"] for j in new] == ["A:2"]
    assert [j["id"] for j in remember(con, [{"id": "Amazon:10", "company": "Amazon"}])] == ["Amazon:10"]


def test_already_alerted_skips_recent_duplicates():
    import sqlite3

    from app.scan import already_alerted
    from app.summary import record_alert
    con = sqlite3.connect(":memory:")
    record_alert(con, {"score": 80, "company": "Kargo",
                       "title": "Machine Learning Engineer", "url": "u"})
    assert already_alerted(con, {"company": "kargo ",
                                 "title": "Machine Learning Engineer"})
    assert not already_alerted(con, {"company": "Kargo", "title": "Data Scientist"})
