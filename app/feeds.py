import csv
import html
import re
from datetime import datetime, timezone

import requests

from app.ats import ROOT

COMPANIES_FILE = ROOT / "data" / "companies.csv"
HEADERS = {"User-Agent": "ResumeFit personal job alerts"}
TIMEOUT = 20


def get_json(url):
    """Download a URL and return its JSON; raise an error on 404 etc."""
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def clean(text):
    """Turn HTML job descriptions into plain text."""
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def make_job(company, job_id, title, location, url, posted, description):
    """One job in the same shape, whichever system it came from."""
    return {"id": f"{company}:{job_id}", "company": company, "title": title,
            "location": location or "", "url": url, "posted": posted or "",
            "description": clean(description)}


def greenhouse(company, slug):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    return [make_job(company, j["id"], j["title"],
                     (j.get("location") or {}).get("name"), j["absolute_url"],
                     j.get("updated_at"), j.get("content"))
            for j in data["jobs"]]


def lever(company, slug):
    data = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    jobs = []
    for j in data:
        posted = datetime.fromtimestamp(j["createdAt"] / 1000, timezone.utc)
        extra = " ".join(item.get("content", "") for item in j.get("lists", []))
        jobs.append(make_job(company, j["id"], j["text"],
                             (j.get("categories") or {}).get("location"),
                             j["hostedUrl"], posted.isoformat(),
                             j.get("descriptionPlain", "") + " " + extra))
    return jobs


def ashby(company, slug):
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    return [make_job(company, j["id"], j["title"], j.get("location"),
                     j["jobUrl"], j.get("publishedAt"),
                     j.get("descriptionPlain") or j.get("descriptionHtml"))
            for j in data["jobs"]]


READERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}


def load_companies():
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fetch_all():
    """Read every company's jobs. Returns (jobs, errors)."""
    jobs, errors = [], []
    for c in load_companies():
        try:
            jobs += READERS[c["source"]](c["company"], c["slug"])
        except Exception as error:
            errors.append(f"{c['company']}: {type(error).__name__}")
    return jobs, errors


if __name__ == "__main__":
    for c in load_companies():
        try:
            count = len(READERS[c["source"]](c["company"], c["slug"]))
            print(f"✅ {c['company']}: {count} jobs")
        except Exception as error:
            print(f"❌ {c['company']} ({c['source']}/{c['slug']}): "
                  f"{type(error).__name__}")