import csv
from collections import Counter

from app.applications import APPS_DIR
from app.ats import ROOT, find_skills

PLAN_FILE = ROOT / "data" / "skill_plan.csv"


def saved_job_descriptions():
    """Read the job description of every saved application."""
    files = sorted(APPS_DIR.glob("*/job_description.txt"))
    return [f.read_text(encoding="utf-8") for f in files]


def skill_gaps(job_descriptions, have, skills):
    """Rank skills you don't have by how many job descriptions ask for them."""
    counts = Counter()
    for jd in job_descriptions:
        counts.update(find_skills(jd, skills) - have)
    total = len(job_descriptions)
    return [{"skill": s, "jobs": n, "percent": round(100 * n / total)}
            for s, n in counts.most_common()]


def load_plan():
    """Read skill_plan.csv into {skill: (project, days)}."""
    with open(PLAN_FILE, encoding="utf-8") as f:
        return {r["skill"]: (r["project"], int(r["days"]))
                for r in csv.DictReader(f)}