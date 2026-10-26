import base64
from pathlib import Path

import app.mail_alerts as mail
import app.scan as scan
from app.notify import format_alert

META = (Path(__file__).parent / "data" / "meta_alert.html").read_text()


def test_meta_alert_email_is_parsed():
    jobs = mail.jobs_in_email(META)
    assert [j["title"] for j in jobs] == [
        "Software Engineer, Machine Learning",
        "Engineering Manager, Machine Learning",
        "Data Scientist, Analytics (Ranking, AI)"]
    first = jobs[0]
    assert first["id"] == "Meta:998357492128826"
    assert first["url"] == "https://www.metacareers.com/jobs/998357492128826"
    assert first["location"].startswith("Sunnyvale, CA")
    assert first["source"] == "email"


def test_other_company_links_and_redirects():
    g = mail.match_job_link("https://www.google.com/about/careers/applications/jobs/results/1234567890-data-scientist?src=email")
    assert g[0] == "Google" and g[1] == "1234567890"
    ms = mail.match_job_link("https://click.example.com/r?u=https%3A%2F%2Fjobs.careers.microsoft.com%2Fglobal%2Fen%2Fjob%2F1789012%2FData-Scientist")
    assert ms[0] == "Microsoft" and ms[1] == "1789012"
    ap = mail.match_job_link("https://jobs.apple.com/en-us/details/200512345-0836/ml-engineer")
    assert ap[0] == "Apple"
    assert mail.match_job_link("https://www.facebook.com/recruiting/unsubscribe/") is None


def test_job_posting_json_ld():
    page = ('<html><script type="application/ld+json">{"@type": "JobPosting", '
            '"description": "<p>Python and SQL</p>", "jobLocation": {"address": '
            '{"addressLocality": "Seattle", "addressRegion": "WA", '
            '"addressCountry": "US"}}}</script></html>')
    posting = mail.job_posting_ld(page)
    assert posting["description"] == "<p>Python and SQL</p>"
    assert mail.ld_location(posting) == "Seattle, WA, US"


def test_gmail_body_is_decoded():
    data = base64.urlsafe_b64encode(META.encode()).decode()
    payload = {"mimeType": "multipart/alternative", "parts": [
        {"mimeType": "text/plain", "body": {"data": base64.urlsafe_b64encode(b"x").decode()}},
        {"mimeType": "text/html", "body": {"data": data}}]}
    assert "metacareers.com/jobs/998357492128826" in mail.html_part(payload)


def test_scan_email_filters_and_alerts(monkeypatch, tmp_path):
    monkeypatch.setenv("GMAIL_REFRESH_TOKEN", "x")
    monkeypatch.setattr(scan, "fetch_alert_jobs", lambda: mail.jobs_in_email(META))

    def fake_description(job):
        if "Data Scientist" in job["title"]:
            job["description"] = "Python SQL statistics machine learning experimentation"
        return job

    monkeypatch.setattr(scan, "add_description", fake_description)
    con = scan.connect(tmp_path / "t.db")
    scan.remember(con, [{"id": "Stripe:1", "company": "Stripe"}])
    matches, errors = scan.scan_email(con)
    titles = [m["title"] for m in matches]
    assert errors == []
    assert "Engineering Manager, Machine Learning" not in titles  # knocked out
    assert "Software Engineer, Machine Learning" in titles      # no description
    assert "Data Scientist, Analytics (Ranking, AI)" in titles  # scored
    assert scan.scan_email(con)[0] == []                         # not repeated
    no_desc = next(m for m in matches if m["ats"] is None)
    text = format_alert(no_desc)
    assert "job-alert email" in text and "open the job to score" in text


def test_scan_email_off_without_token(monkeypatch, tmp_path):
    monkeypatch.delenv("GMAIL_REFRESH_TOKEN", raising=False)
    assert scan.scan_email(scan.connect(tmp_path / "t.db")) == ([], [])
