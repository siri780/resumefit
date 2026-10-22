import sqlite3
from datetime import datetime

from app.applications import TIMEZONE
from app.ats import ROOT, load_skills
from app.bases import pick_base
from app.feeds import fetch_all, job_description
from app.rank import assess, is_relevant
from app.tailor import load_approved

DB = ROOT / "data" / "jobs.db"


def connect(path=DB):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS seen "
                "(id TEXT PRIMARY KEY, first_seen TEXT)")
    return con


def remember(con, jobs):
    """Save job ids; return only the jobs never seen before."""
    now = datetime.now(TIMEZONE).isoformat(timespec="minutes")
    known = {row[0] for row in con.execute("SELECT id FROM seen")}
    new = [j for j in jobs if j["id"] not in known]
    con.executemany("INSERT OR IGNORE INTO seen VALUES (?, ?)",
                    [(j["id"], now) for j in new])
    con.commit()
    return new


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


if __name__ == "__main__":
    matches, errors, total = scan()
    print(f"Checked {total} jobs · {len(matches)} new matches · {len(errors)} errors")
    for m in matches[:10]:
        print(f"[{m['score']}] {m['tier']:<9} {m['ats']}% ({m['base']})  {m['company']} - "
              f"{m['title']}  ({m['location']})\n      {m['url']}")