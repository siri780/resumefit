import app.feeds as feeds


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_amazon_reader(monkeypatch):
    job = {"id_icims": "123", "title": "Data Scientist I",
           "normalized_location": "Bellevue, Washington, USA",
           "job_path": "/en/jobs/123/data-scientist", "posted_date": "October 23, 2026",
           "description": "Build models.", "basic_qualifications": "- SQL",
           "preferred_qualifications": "- Python"}
    monkeypatch.setattr(feeds.requests, "get",
                        lambda *a, **k: FakeResponse({"jobs": [job]}))
    jobs = feeds.amazon("Amazon")
    assert len(jobs) == 1  # same job from every search is kept once
    j = jobs[0]
    assert j["id"] == "Amazon:123"
    assert j["url"] == "https://www.amazon.jobs/en/jobs/123/data-scientist"
    assert "SQL" in j["description"] and "Python" in j["description"]
    assert j["location"] == "Bellevue, Washington, USA"


def test_slow_sources_skipped_between_big_scans(monkeypatch):
    monkeypatch.setattr(feeds, "load_companies", lambda: [
        {"company": "Amazon", "source": "amazon", "slug": ""},
        {"company": "X", "source": "greenhouse", "slug": "x"}])
    called = []
    monkeypatch.setitem(feeds.READERS, "amazon", lambda c, s: called.append(c) or [])
    monkeypatch.setitem(feeds.READERS, "greenhouse", lambda c, s: called.append(c) or [])
    feeds.fetch_all(include_workday=False)
    assert called == ["X"]


def test_workday_skips_half_empty_entries(monkeypatch):
    class Resp(FakeResponse):
        pass

    posts = {"jobPostings": [{"title": "Data Scientist", "externalPath": "/job/1",
                              "locationsText": "Santa Clara, CA"},
                             {"externalPath": "/job/2"}, {"title": "No path"}]}
    monkeypatch.setattr(feeds.requests, "post", lambda *a, **k: Resp(posts))
    jobs = feeds.workday("Intel", "https://intel.wd1.myworkdayjobs.com/External")
    assert [j["id"] for j in jobs] == ["Intel:/job/1"]
