from datetime import datetime

import app.summary as summary
from app.scan import connect


def test_summary_counts_and_best_jobs(tmp_path):
    con = connect(tmp_path / "t.db")
    summary.record_alert(con, {"score": 60, "company": "Meta", "title": "DS", "url": "u1"})
    summary.record_alert(con, {"score": 90, "company": "Stripe", "title": "SWE", "url": "u2"})
    summary.bump(con, "tailored", 2)
    text = summary.summary_text(con)
    assert "Job alerts sent: 2" in text and "Resumes tailored: 2" in text
    assert text.index("Stripe") < text.index("Meta")   # best match first


def test_summary_sent_once_after_8pm(monkeypatch, tmp_path):
    con = connect(tmp_path / "t.db")
    sent = []

    class Late(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 26, 20, 30, tzinfo=tz)

    monkeypatch.setattr(summary, "datetime", Late)
    assert summary.maybe_send_summary(con, sent.append) is True
    assert summary.maybe_send_summary(con, sent.append) is False
    assert len(sent) == 1
