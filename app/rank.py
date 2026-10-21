import re

ROLE_WORDS = ["data scientist", "data science", "machine learning", "ml engineer",
              "data analyst", "analytics", "software engineer", "ai engineer",
              "applied scientist", "research scientist", "quantitative", "quant ",
              "data engineer", "statistician", "decision scientist"]
SKIP_TITLE = ["intern", "internship", "co-op"]
BLOCKERS = ["u.s. citizen", "us citizen", "citizenship is required",
            "security clearance", "secret clearance", "green card holder"]
NO_SPONSOR = ["not sponsor", "no sponsorship", "unable to sponsor",
              "without sponsorship", "not provide sponsorship",
              "not offer sponsorship"]
YES_SPONSOR = ["visa sponsorship", "will sponsor", "h-1b", "h1b"]
FLEXIBLE = ["or equivalent", "master's", "masters", "ms in", "m.s."]
TARGET_WORDS = ["new grad", "new college grad", "university grad", "early career",
                "entry level", "entry-level", "2027", "junior", "associate"]
REACH_WORDS = ["senior", "sr.", "sr ", "lead"]
LONGSHOT_WORDS = ["staff", "principal", "director", "head of", "manager",
                  "distinguished"]
FOREIGN = ["india", "london", "united kingdom", "canada", "toronto", "vancouver",
           "singapore", "dublin", "ireland", "germany", "berlin", "amsterdam",
           "netherlands", "sydney", "australia", "tokyo", "japan", "hong kong",
           "paris", "france", "bengaluru", "bangalore", "hyderabad", "poland",
           "mexico", "brazil", "israel", "zurich", "switzerland", "spain",
           "china", "shanghai", "seoul", "korea"]

MIN_MATCH = {"Target": 0, "Stretch": 60, "Reach": 75, "Long shot": 85}
TIER_POINTS = {"Target": 100, "Stretch": 70, "Reach": 40, "Long shot": 15}


def has_any(text, words):
    return any(w in text for w in words)


def is_relevant(job):
    """Quick check on title + location, before fetching descriptions."""
    title = f" {job['title'].lower()} "
    location = job["location"].lower()
    if not has_any(title, ROLE_WORDS) or has_any(title, SKIP_TITLE):
        return False
    us_mentioned = "united states" in location or "usa" in location or "remote" in location
    return us_mentioned or not has_any(location, FOREIGN)


def years_required(text):
    """Smallest number of years asked for, e.g. '3+ years' -> 3."""
    found = re.findall(r"(\d{1,2})\s*(?:\+|-\s*\d{1,2}|to\s*\d{1,2})?\s*(?:years|yrs)",
                       text.lower())
    return min(int(n) for n in found) if found else None


def tier(job):
    title = f" {job['title'].lower()} "
    if has_any(title, LONGSHOT_WORDS):
        return "Long shot"
    if has_any(title, REACH_WORDS):
        return "Reach"
    if has_any(title, TARGET_WORDS) or re.search(r"\b(i|1)\s*$", title.strip()):
        return "Target"
    years = years_required(job["description"])
    if years is None:
        return "Stretch"
    if years <= 2:
        return "Target"
    return "Stretch" if years <= 5 else "Reach"


def assess(job, ats_percent):
    """Decide tier, sponsorship, blockers and an overall score for one job."""
    text = job["description"].lower()
    job_tier = tier(job)
    blocked = [w for w in BLOCKERS if w in text]
    if has_any(text, NO_SPONSOR):
        sponsor, sponsor_points = "⚠️ says no sponsorship (OPT may still work)", 30
    elif has_any(text, YES_SPONSOR):
        sponsor, sponsor_points = "✅ sponsorship mentioned", 100
    else:
        sponsor, sponsor_points = "❔ not mentioned", 50
    flexible = has_any(text, FLEXIBLE)
    score = round(0.50 * ats_percent + 0.20 * TIER_POINTS[job_tier]
                  + 0.15 * (100 if flexible else 0) + 0.10 * sponsor_points + 5)
    show = not blocked and ats_percent >= MIN_MATCH[job_tier]
    return {"tier": job_tier, "sponsorship": sponsor, "flexible": flexible,
            "blocked": blocked, "score": score, "show": show}