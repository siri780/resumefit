import os
import sqlite3
from datetime import datetime

from app.applications import TIMEZONE
from app.ats import ROOT, load_skills
from app.bases import DEFAULT, guess_base, pick_base
from app.mail_alerts import add_description, fetch_alert_jobs
from app.feeds import fetch_all, job_description
from app.rank import assess, is_relevant, knockouts, tier
from app.tailor import load_approved

DB = ROOT / "data" / "jobs.db"


def connect(path=DB):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS seen "
                "(id TEXT PRIMARY KEY, first_seen TEXT)")
    return con


def remember(con, jobs, seed_new_companies=True):
    """Save job ids; return only the jobs never seen before."""
    now = datetime.now(TIMEZONE).isoformat(timespec="minutes")
    known = {row[0] for row in con.execute("SELECT id FROM seen")}
    known_companies = {k.split(":", 1)[0] for k in known}
    new = [j for j in jobs if j["id"] not in known]
    # A company seen for the first time is saved silently, so adding a big
    # board (like Amazon) doesn't flood you with hundreds of old jobs.
    fresh = [j for j in new
             if not seed_new_companies
             or j["id"].split(":", 1)[0] in known_companies or not known]
    con.executemany("INSERT OR IGNORE INTO seen VALUES (?, ?)",
                    [(j["id"], now) for j in new])
    con.commit()
    return fresh


def scan(include_workday=True):
    """Find new, relevant, well-matched jobs. Returns (matches, errors, total)."""
    jobs, errors = fetch_all(include_workday)
    con = connect()
    first_run = con.execute("SELECT COUNT(*) FROM seen").fetchone()[0] == 0
    new = remember(con, jobs)
    if first_run:
        return [], errors, len(jobs)

    skills = load_skills()
    texts = {}
    matches = []
    for job in new:
        if not is_relevant(job):
            continue
        job_description(job)
        base, ats, how = pick_base(job["title"], job["description"], skills,
                                   texts)
        result = assess(job, ats["percent"])
        if result["show"]:
            matches.append({**job, **result, "ats": ats["percent"],
                            "missing": ats["missing"], "base": base,
                            "base_how": how})
    return sorted(matches, key=lambda m: m["score"], reverse=True), errors, len(jobs)


def scan_email(con):
    """New jobs from big-company job-alert emails. Returns (matches, errors)."""
    if not os.getenv("GMAIL_REFRESH_TOKEN"):
        return [], []
    try:
        jobs = fetch_alert_jobs()
    except Exception as error:
        return [], [f"Gmail: {type(error).__name__}"]
    new = remember(con, jobs, seed_new_companies=False)
    skills = load_skills()
    texts = {}
    matches = []
    for job in new:
        if not is_relevant(job):
            continue
        add_description(job)
        if job["description"]:
            base, ats, how = pick_base(job["title"], job["description"],
                                       skills, texts)
            result = assess(job, ats["percent"])
            if result["show"]:
                matches.append({**job, **result, "ats": ats["percent"],
                                "missing": ats["missing"], "base": base,
                                "base_how": how})
        elif not knockouts(job) and tier(job) != "Long shot":
            # The page didn't share its description: still alert you, using
            # the title and location checks only.
            matches.append({**job, "tier": tier(job), "ats": None,
                            "missing": [], "score": 50,
                            "base": guess_base(job["title"]) or DEFAULT,
                            "base_how": "title",
                            "sponsorship": "❔ open the job to check"})
    return matches, []


if __name__ == "__main__":
    matches, errors, total = scan()
    print(f"Checked {total} jobs · {len(matches)} new matches · {len(errors)} errors")
    for m in matches[:10]:
        print(f"[{m['score']}] {m['tier']:<9} {m['ats']}% ({m['base']})  {m['company']} - "
              f"{m['title']}  ({m['location']})\n      {m['url']}")