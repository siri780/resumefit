"""Keyword match: how much of the job's own wording your resume uses.

The ATS score only counts skills (Python, SQL, ...). Real screening tools
and recruiters also look for the job's other important words, like
"fraud", "forecasting" or "stakeholders". This score measures those, so
you can see what a tailored rewording actually changed.
"""
import re
from collections import Counter

TOP_N = 25

STOPWORDS = set("""
a about above across after again against all also am an and any are as at be
because been before being below between both but by can could did do does doing
down during each few for from further had has have having he her here hers him
his how i if in into is it its itself just me more most my no nor not now of off
on once only or other our ours out over own same she should so some such than
that the their them then there these they this those through to too under until
up very was we were what when where which while who whom why will with within
would you your yours etc e.g i.e via per
able ability across additional along applicants apply benefits best candidate
candidates company compensation culture day days degree description employer
employment equal opportunity environment experience experiences field focus
great help including include includes job jobs join key level like looking
make means minimum must new offer one opportunities opportunity part people
plus position preferred qualifications qualified related required requirements
responsibilities responsible role roles salary skills strong support team teams
time two using use well work working world year years ability abilities will
based within across every high highly provide providing ensure using also may
range pay base bonus equity insurance health medical dental vision leave paid
location locations office remote hybrid onsite status gender race religion
national origin veteran disability age sexual orientation identity color law
applicable accommodation please information visit www com http https
need needs home hour hours individual individuals on-demand provide provides
service services within want wants seeking seek etc inc llc corporation
""".split())
KEEP_SLASH = {"a/b", "ci/cd", "tcp/ip", "r/d"}


def stem(word):
    if word.endswith("ss"):
        return word
    for suffix in ("ations", "ation", "ments", "ment", "ings", "ing", "ies",
                   "ers", "er", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def words(text):
    out = []
    for token in re.findall(r"[a-z][a-z+#/.-]*[a-z+#]|[a-z]", text.lower()):
        out += [token] if token in KEEP_SLASH else token.split("/")
    return [w.strip(".-") for w in out if w.strip(".-")]


def important_terms(jd_text, top_n=TOP_N, exclude=()):
    """The job's most-repeated meaningful words (stemmed)."""
    skip = STOPWORDS | {w.lower() for name in exclude for w in words(name)}
    counts = Counter(stem(w) for w in words(jd_text)
                     if (len(w) >= 3 or w in KEEP_SLASH) and w not in skip)
    return [term for term, _ in counts.most_common(top_n)]


def keyword_match(resume_text, jd_text, company=""):
    """Return {"percent", "matched", "missing"} for the job's key words."""
    terms = important_terms(jd_text, exclude=[company] if company else ())
    have = {stem(w) for w in words(resume_text)}
    shown = {}
    for w in words(jd_text):                 # readable form of each stem
        shown.setdefault(stem(w), w)
    matched = [shown.get(t, t) for t in terms if t in have]
    missing = [shown.get(t, t) for t in terms if t not in have]
    percent = round(100 * len(matched) / len(terms)) if terms else 0
    return {"percent": percent, "matched": matched, "missing": missing}
