from datetime import timedelta

from app.scan import connect
from app.watch import due


def test_due_only_after_interval(tmp_path):
    con = connect(tmp_path / "t.db")
    every = timedelta(minutes=5)
    assert due(con, "scan", every) is True
    assert due(con, "scan", every) is False
    assert due(con, "scan", timedelta(0)) is True
