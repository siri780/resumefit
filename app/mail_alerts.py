"""Turn job-alert emails into ResumeFit alerts.

Google, Microsoft, Meta and Apple don't offer a job feed we can read, but
they email you job alerts, and so does LinkedIn. This reads those emails
(read-only), pulls out each job, and sends it through the same filters,
scoring and Telegram alerts as every other job.
"""
import base64
import html
import json
import os
import re
from html.parser import HTMLParser
from urllib.parse import unquote

import requests

from app.feeds import HEADERS, TIMEOUT, clean

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Only emails from these senders are read.
QUERY = ("newer_than:2d (from:recruiting.facebook.com OR from:metacareers.com "
         "OR from:careers.microsoft.com OR from:microsoft.com "
         "OR from:careers.google.com OR from:google.com OR from:apple.com) "
         "-from:accounts.google.com -from:noreply-accounts@google.com")

LINKEDIN_QUERY = "newer_than:2d from:jobalerts-noreply@linkedin.com"
# Staffing/training firms that post look-alike jobs on LinkedIn.
LINKEDIN_SKIP = {"synergisticit"}
LINKEDIN_BADGES = re.compile(
    r"^(?:top applicant|apply with resume.*|easy apply|promoted|actively recruiting|"
    r"this company is actively hiring|be an early applicant|\d+ (?:school )?alum.*|"
    r"\d+ connections?.*|your profile matches.*|.*applicants?|new)$", re.I)
LINKEDIN_VIEW = re.compile(r"View job:\s*https?://(?:www\.)?linkedin\.com/(?:comm/)?jobs/view/(\d+)")

# Job links we recognise, per company.
JOB_LINKS = [
    ("Meta", re.compile(r"https?://(?:www\.)?metacareers\.com/(?:v2/)?jobs/(\d{6,})")),
    ("Meta", re.compile(r"https?://(?:www\.)?metacareers\.com/profile/job_details/(\d{6,})")),
    ("Google", re.compile(r"https?://(?:www\.)?google\.com/about/careers/applications/jobs/results/(\d{6,})[^\s\"'<>]*")),
    ("Google", re.compile(r"https?://careers\.google\.com/jobs/results/(\d{6,})[^\s\"'<>]*")),
    ("Microsoft", re.compile(r"https?://jobs\.careers\.microsoft\.com/[^\s\"'<>]*?/job/(\d{5,})")),
    ("Microsoft", re.compile(r"https?://apply\.careers\.microsoft\.com/careers/job/(\d{5,})")),
    ("Apple", re.compile(r"https?://jobs\.apple\.com/[a-z-]+/details/([0-9A-Za-z-]{6,})")),
]


def gmail_service():
    """Connect to Gmail (read-only) using your saved secrets."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=GMAIL_SCOPES,
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# ---------- Reading the emails ----------
def html_part(payload, prefer="text/html"):
    """Find the HTML (or plain text) body inside a Gmail message."""
    other = "text/plain" if prefer == "text/html" else "text/html"
    found = {}

    def walk(part):
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data")
        if data and mime in ("text/html", "text/plain"):
            found.setdefault(mime, base64.urlsafe_b64decode(data).decode(
                "utf-8", "replace"))
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return found.get(prefer) or found.get(other, "")


class LinkReader(HTMLParser):
    """Collect (link, link text, text that follows) from an email."""

    def __init__(self):
        super().__init__()
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._close()
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.links.append([self._href, " ".join(self._text).strip(), ""])
            self._href = None

    def handle_data(self, data):
        if self._href:
            self._text.append(data.strip())
        elif self.links:
            self.links[-1][2] += " " + data.strip()

    def _close(self):
        if self._href:
            self.links.append([self._href, " ".join(self._text).strip(), ""])
            self._href = None


def match_job_link(href):
    """Return (company, job_id, clean_url) if the link is a job page."""
    for candidate in (href, unquote(href), unquote(unquote(href))):
        for company, pattern in JOB_LINKS:
            m = pattern.search(candidate)
            if m:
                url = m.group(0).split("?")[0]
                return company, m.group(1), url
    return None


def jobs_in_email(body, received=""):
    """Every job linked from one alert email."""
    reader = LinkReader()
    reader.feed(body)
    reader._close()
    jobs, seen = [], set()
    for href, text, after in reader.links:
        hit = match_job_link(html.unescape(href or ""))
        title = re.sub(r"\s+", " ", text).strip()
        if not hit or not title or title.lower() in ("view job", "apply",
                                                     "view all", "learn more"):
            continue
        company, job_id, url = hit
        if (company, job_id) in seen:
            continue
        seen.add((company, job_id))
        location = re.sub(r"\s+", " ", after).strip()[:200]
        jobs.append({"id": f"{company}:{job_id}", "company": company,
                     "title": title, "location": location, "url": url,
                     "posted": received, "description": "",
                     "source": "email"})
    return jobs


def linkedin_jobs_in_email(text, received=""):
    """Every job in one LinkedIn job-alert email (plain-text version).

    Each job is a block: title, company, location, a few badges, then
    "View job: https://www.linkedin.com/comm/jobs/view/<id>/...".
    """
    jobs, seen = [], set()
    lines = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        m = LINKEDIN_VIEW.search(line)
        if m:
            info = [x for x in lines if not LINKEDIN_BADGES.match(x)
                    and not x.lower().startswith("your job alert for")]
            job_id = m.group(1)
            if len(info) >= 2 and job_id not in seen:
                seen.add(job_id)
                company = info[1]
                if company.lower().replace(" ", "") not in LINKEDIN_SKIP:
                    jobs.append({
                        "id": f"LinkedIn:{job_id}", "company": company,
                        "title": info[0],
                        "location": info[2] if len(info) > 2 else "",
                        "url": f"https://www.linkedin.com/jobs/view/{job_id}/",
                        "posted": received, "description": "",
                        "source": "email", "via": "LinkedIn"})
            lines = []
        elif line.startswith("---"):
            lines = []
        elif line:
            lines.append(line)
    return jobs


def fetch_alert_jobs(service=None, max_emails=30):
    """Jobs from the job-alert emails of the last 2 days."""
    service = service or gmail_service()
    jobs = []
    for query, reader, prefer in ((QUERY, jobs_in_email, "text/html"),
                                  (LINKEDIN_QUERY, linkedin_jobs_in_email,
                                   "text/plain")):
        listing = service.users().messages().list(
            userId="me", q=query, maxResults=max_emails).execute()
        for ref in listing.get("messages", []):
            msg = service.users().messages().get(
                userId="me", id=ref["id"], format="full").execute()
            jobs += reader(html_part(msg["payload"], prefer),
                           msg.get("internalDate", ""))
    return jobs


# ---------- Getting the full job description ----------
def job_posting_ld(page):
    """Find the schema.org JobPosting data many job pages include."""
    for raw in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>',
                          page, flags=re.S | re.I):
        try:
            data = json.loads(raw.strip())
        except ValueError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data])
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item
    return None


def ld_location(posting):
    places = posting.get("jobLocation") or []
    places = places if isinstance(places, list) else [places]
    names = []
    for p in places:
        addr = (p or {}).get("address") or {}
        if isinstance(addr, dict):
            parts = [addr.get("addressLocality"), addr.get("addressRegion"),
                     addr.get("addressCountry") if isinstance(
                         addr.get("addressCountry"), str) else None]
            names.append(", ".join(x for x in parts if x))
    return "; ".join(n for n in names if n)


LINKEDIN_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9"}
VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "wbr", "source"}


class _DescriptionReader(HTMLParser):
    """Text inside LinkedIn's job-description box."""

    def __init__(self):
        super().__init__()
        self.depth, self.parts = 0, []

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class") or ""
        if tag in VOID_TAGS:
            if self.depth:
                self.parts.append(" ")
            return
        if self.depth:
            self.depth += 1
        elif tag == "div" and ("show-more-less-html__markup" in cls
                               or "description__text" in cls):
            self.depth = 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)


def linkedin_description(job):
    """Fill in a LinkedIn job's description from LinkedIn's public job page."""
    job_id = job["id"].split(":", 1)[1]
    for url in (f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}",
                f"https://www.linkedin.com/jobs/view/{job_id}/"):
        try:
            response = requests.get(url, headers=LINKEDIN_HEADERS, timeout=TIMEOUT)
        except requests.RequestException:
            continue
        if not response.ok:
            continue
        posting = job_posting_ld(response.text)
        if posting and isinstance(posting.get("description"), str):
            job["description"] = clean(posting["description"])
            job["location"] = ld_location(posting) or job["location"]
            return job
        reader = _DescriptionReader()
        reader.feed(response.text)
        text = clean(" ".join(reader.parts))
        if len(text) > 200:
            job["description"] = text
            return job
    return job


def add_description(job):
    """Fill in the description (and location) from the job page if we can."""
    if job.get("via") == "LinkedIn":
        return linkedin_description(job)
    try:
        response = requests.get(job["url"], headers=HEADERS, timeout=TIMEOUT)
        if not response.ok:
            return job
        posting = job_posting_ld(response.text)
    except requests.RequestException:
        return job
    if posting:
        parts = [posting.get("description"), posting.get("qualifications"),
                 posting.get("responsibilities")]
        job["description"] = clean(" ".join(p for p in parts if isinstance(p, str)))
        job["location"] = ld_location(posting) or job["location"]
    return job


if __name__ == "__main__":
    # Quick check from your codespace: python -m app.mail_alerts <linkedin job id>
    import sys

    if len(sys.argv) > 1:
        test = linkedin_description({"id": f"LinkedIn:{sys.argv[1]}",
                                     "location": "", "description": ""})
        print(f"Description: {len(test['description'])} characters")
        print(test["description"][:400])
