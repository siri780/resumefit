from app.ats import alias_pattern, find_skills, load_skills, score


def test_ml_does_not_match_inside_html():
    assert alias_pattern("ml", False).search("I know HTML") is None
    assert alias_pattern("ml", False).search("I know ML") is not None


def test_r_is_case_sensitive_and_ignores_r_and_d():
    pat = alias_pattern("R", True)
    assert pat.search("Python, R, SQL") is not None
    assert pat.search("worked in R&D") is None
    assert pat.search("data science") is None


def test_aliases_map_to_one_skill():
    skills = load_skills()
    assert find_skills("used sklearn daily", skills) == {"scikit-learn"}


def test_score_perfect_match():
    result = score("Python and SQL", "Need Python and SQL")
    assert result["percent"] == 100
    assert result["missing"] == []