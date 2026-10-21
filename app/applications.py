import csv
import re
import shutil
from datetime import date

from app.ats import ROOT

APPS_DIR = ROOT / "applications"
TRACKER = APPS_DIR / "_Tracker.csv"
FIELDS = ["date", "company", "role", "ats_before", "ats_after",
          "status", "link", "folder", "notes"]


def read_tracker():
    """Return all saved applications as a list of dictionaries."""
    if not TRACKER.exists():
        return []
    with open(TRACKER, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def already_applied(company, role):
    """True if this company + role is already in the tracker."""
    key = (company.strip().lower(), role.strip().lower())
    return any((r["company"].strip().lower(), r["role"].strip().lower()) == key
               for r in read_tracker())

def safe_part(text):
    """Turn text into a safe folder-name part."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_") or "Unknown"


def save_application(company, role, jd, tex, pdf_path, before, after, link=""):
    """Save PDF, .tex, job description and ATS report; add a tracker row."""
    APPS_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()
    folder = APPS_DIR / f"{today}_{safe_part(company)}_{safe_part(role)}"
    folder.mkdir(exist_ok=True)

    shutil.copy(pdf_path, folder / pdf_path.name)
    (folder / "resume.tex").write_text(tex, encoding="utf-8")
    (folder / "job_description.txt").write_text(jd, encoding="utf-8")
    report = (f"ATS before: {before['percent']}%\n"
              f"ATS after: {after['percent']}%\n"
              f"Matched: {', '.join(after['matched'])}\n"
              f"Missing: {', '.join(after['missing'])}\n")
    (folder / "ats_report.txt").write_text(report, encoding="utf-8")

    new_file = not TRACKER.exists()
    with open(TRACKER, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "date": today, "company": company, "role": role,
            "ats_before": before["percent"], "ats_after": after["percent"],
            "status": "Applied", "link": link,
            "folder": folder.name, "notes": "",
        })
    return folder