import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_FILE = ROOT / "data" / "skills.csv"


def load_skills():
    """Read skills.csv into a list of dictionaries."""
    skills = []
    with open(SKILLS_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            skills.append({
                "skill": row["skill"],
                "aliases": row["aliases"].split("|"),
                "category": row["category"],
                "case_sensitive": row["case_sensitive"] == "yes",
            })
    return skills


def latex_to_text(tex):
    """Keep only the resume body and strip LaTeX commands."""
    start = tex.find("\\begin{document}")
    end = tex.find("\\end{document}")
    if start != -1 and end != -1:
        tex = tex[start:end]
    tex = re.sub(r"\\[a-zA-Z]+", " ", tex)
    tex = tex.replace("{", " ").replace("}", " ").replace("\\", "")
    return tex


def alias_pattern(alias, case_sensitive):
    """Build a regex that matches the alias only as a whole word."""
    pattern = r"(?<![A-Za-z0-9&])" + re.escape(alias) + r"(?![A-Za-z0-9&])"
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)


def find_skills(text, skills):
    """Return the set of standard skill names found in text."""
    found = set()
    for s in skills:
        for alias in s["aliases"]:
            if alias_pattern(alias, s["case_sensitive"]).search(text):
                found.add(s["skill"])
                break
    return found


def score(resume_text, jd_text, skills=None):
    """Compare resume and job description; return %, matched and missing."""
    if skills is None:
        skills = load_skills()
    jd_skills = find_skills(jd_text, skills)
    resume_skills = find_skills(resume_text, skills)
    matched = sorted(jd_skills & resume_skills)
    missing = sorted(jd_skills - resume_skills)
    percent = round(100 * len(matched) / len(jd_skills)) if jd_skills else 0
    return {"percent": percent, "matched": matched, "missing": missing}


if __name__ == "__main__":
    resume = latex_to_text((ROOT / "data" / "resume_ds.tex").read_text(encoding="utf-8"))
    jd = (ROOT / "data" / "sample_jd.txt").read_text(encoding="utf-8")
    result = score(resume, jd)
    print(f"ATS score: {result['percent']}%")
    print("Matched:", ", ".join(result["matched"]))
    print("Missing:", ", ".join(result["missing"]))