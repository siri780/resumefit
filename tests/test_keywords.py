from app.keywords import important_terms, keyword_match, stem


def test_stemming_keeps_business():
    assert stem("business") == "business"
    assert stem("forecasting") == "forecast"


def test_company_name_and_filler_ignored():
    jd = "Humana is hiring. Forecasting forecasting fraud fraud insights. Benefits and salary."
    terms = important_terms(jd, exclude=["Humana"])
    assert "humana" not in terms and "salary" not in terms
    assert terms[:2] == ["forecast", "fraud"]


def test_rewording_raises_keyword_match():
    jd = "Detect fraud. Fraud insights. Communicate insights to stakeholders."
    before = keyword_match("Built dashboards for managers.", jd)
    after = keyword_match("Built fraud dashboards and communicated insights to stakeholders.", jd)
    assert after["percent"] > before["percent"]
    assert "a/b" in important_terms("Run A/B tests. A/B testing at scale.")
