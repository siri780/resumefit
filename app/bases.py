"""The three base resumes and how to pick the right one for a job."""
import re

from app.ats import ROOT, latex_to_text, score

BASES = {
    "Data Scientist": "resume_ds.tex",
    "ML Engineer": "resume_mle.tex",
    "Software Engineer": "resume_swe.tex",
}
DEFAULT = "Data Scientist"

# Checked in this order, so "Software Engineer, Machine Learning" -> ML Engineer.
TITLE_HINTS = [
    ("ML Engineer", ["machine learning", "ml engineer", "mle", "ai engineer",
                     "applied scientist", "deep learning", "llm", "nlp",
                     "computer vision", "genai", "generative ai"]),
    ("Software Engineer", ["software", "developer", "backend", "back-end",
                           "full stack", "full-stack", "fullstack", "sde",
                           "swe", "platform engineer", "data engineer"]),
    ("Data Scientist", ["data scien", "analyst", "analytics", "statistic",
                        "quantitative", "research scientist", "decision scien"]),
]


def base_path(name):
    return ROOT / "data" / BASES[name]


def load_base(name):
    """Return the LaTeX of one base resume."""
    return base_path(name).read_text(encoding="utf-8")


def guess_base(title):
    """Pick a base resume from a job title, or None if the title is unclear."""
    t = title.lower()
    for name, hints in TITLE_HINTS:
        if any(re.search(r"\b" + re.escape(h), t) for h in hints):
            return name
    return None


def pick_base(title, jd, skills, texts=None):
    """Return (name, ats_result, how).

    A clear title decides the base on its own (how="title").
    An unclear title falls back to the base that best matches the job
    description (how="match")."""
    texts = {} if texts is None else texts

    def text_of(name):
        if name not in texts:
            texts[name] = latex_to_text(load_base(name))
        return texts[name]

    name = guess_base(title)
    if name:
        return name, score(text_of(name), jd, skills), "title"
    results = {n: score(text_of(n), jd, skills) for n in BASES}
    name = max(results, key=lambda n: (results[n]["percent"], n == DEFAULT))
    return name, results[name], "match"
