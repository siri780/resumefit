import csv
import html
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from app.ats import ROOT

COMPANIES_FILE = ROOT / "data" / "companies.csv"
HEADERS = {"User-Agent": "ResumeFit personal job alerts"}
TIMEOUT = 20
SEARCHES = ["data scientist", "machine learning", "data analyst",
            "software engineer"]


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


def workday_parts(careers_url):
    """Split a Workday careers URL into host, tenant and site."""
    url = urlparse(careers_url)
    host = url.netloc
    tenant = host.split(".")[0]
    site = url.path.strip("/").split("/")[-1]
    return host, tenant, site


def workday(company, careers_url):
    host, tenant, site = workday_parts(careers_url)
    api = f"https://{host}/wday/cxs/{tenant}/{site}"
    jobs, seen = [], set()
    for query in SEARCHES:
        response = requests.post(
            f"{api}/jobs", headers=HEADERS, timeout=TIMEOUT,
            json={"appliedFacets": {}, "limit": 20, "offset": 0,
                  "searchText": query})
        response.raise_for_status()
        for j in response.json().get("jobPostings", []):
            path = j["externalPath"]
            if path in seen:
                continue
            seen.add(path)
            job = make_job(company, path, j["title"], j.get("locationsText"),
                           f"https://{host}/{site}{path}", j.get("postedOn"), "")
            job["detail_api"] = f"{api}{path}"
            jobs.append(job)
    return jobs


def job_description(job):
    """Fetch a Workday job's description only when it's actually needed."""
    if job["description"] or not job.get("detail_api"):
        return job["description"]
    info = get_json(job["detail_api"]).get("jobPostingInfo", {})
    job["description"] = clean(info.get("jobDescription"))
    places = [info.get("location")] + list(info.get("additionalLocations") or [])
    country = (info.get("country") or {}).get("descriptor")
    places = [p for p in places + [country] if p]
    if places:
        job["location"] = "; ".join(places)
    return job["description"]


def amazon(company, slug=""):
    """Amazon's public job search (U.S. only, newest first)."""
    jobs, seen = [], set()
    for query in SEARCHES:
        response = requests.get(
            "https://www.amazon.jobs/en/search.json", headers=HEADERS,
            timeout=TIMEOUT,
            params={"base_query": query, "country": "USA",
                    "result_limit": 100, "sort": "recent"})
        response.raise_for_status()
        for j in response.json().get("jobs", []):
            if j["id_icims"] in seen:
                continue
            seen.add(j["id_icims"])
            description = " ".join(filter(None, [
                j.get("description"),
                "Basic qualifications:", j.get("basic_qualifications"),
                "Preferred qualifications:", j.get("preferred_qualifications")]))
            jobs.append(make_job(
                company, j["id_icims"], j["title"],
                j.get("normalized_location") or j.get("location"),
                "https://www.amazon.jobs" + j["job_path"],
                j.get("posted_date"), description))
    return jobs


READERS = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby,
           "workday": workday, "amazon": amazon}
SLOW_SOURCES = {"workday", "amazon"}  # big boards: checked every ~30 minutes


def load_companies():
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fetch_all(include_workday=True):
    """Read every company's jobs. Returns (jobs, errors)."""
    jobs, errors = [], []
    for c in load_companies():
        if c["source"] in SLOW_SOURCES and not include_workday:
            continue
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