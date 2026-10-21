import app.applications as apps

RESULT = {"percent": 70, "matched": ["Python"], "missing": ["AWS"]}


def use_temp_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(apps, "APPS_DIR", tmp_path)
    monkeypatch.setattr(apps, "TRACKER", tmp_path / "_Tracker.csv")


def fake_pdf(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"%PDF fake")
    return pdf


def test_save_creates_folder_and_tracker_row(monkeypatch, tmp_path):
    use_temp_folder(monkeypatch, tmp_path)
    folder = apps.save_application("Pinterest", "Data Scientist", "JD text",
                                   "tex", fake_pdf(tmp_path), RESULT, RESULT)

    assert (folder / "test.pdf").exists()
    assert (folder / "job_description.txt").read_text() == "JD text"
    rows = apps.read_tracker()
    assert len(rows) == 1
    assert rows[0]["company"] == "Pinterest"
    assert rows[0]["status"] == "Applied"


def test_already_applied_ignores_case_and_spaces(monkeypatch, tmp_path):
    use_temp_folder(monkeypatch, tmp_path)
    apps.save_application("Pinterest", "Data Scientist", "JD", "tex",
                          fake_pdf(tmp_path), RESULT, RESULT)

    assert apps.already_applied(" pinterest ", "DATA SCIENTIST")
    assert not apps.already_applied("Adobe", "Data Scientist")