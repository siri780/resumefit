from app.ats import ROOT, alias_pattern, find_skills, latex_to_text, load_skills, score

def test_mentored_counts_as_leadership():
    assert "Leadership" in find_skills("mentored 50+ students", load_skills())


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


def test_leadership_found_in_resume():
    resume_path = ROOT / "data" / "resume.tex"
    resume_tex = resume_path.read_text(encoding="utf-8")
    resume_text = latex_to_text(resume_tex)

    assert "Leadership" in find_skills(resume_text, load_skills())

def test_link_targets_are_not_resume_text():
    tex = "\\begin{document}\\href{https://github.com/x/resumefit}{\\underline{GitHub}}\\end{document}"
    text = latex_to_text(tex)
    assert "GitHub" in text and "resumefit" not in text
