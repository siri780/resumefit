from app.ats import load_skills
from app.skill_gaps import skill_gaps

JDS = [
    "Need Python, AWS and Spark.",
    "Python and AWS required.",
    "SQL and AWS preferred.",
]


def test_ranks_missing_skills_by_frequency():
    gaps = skill_gaps(JDS, {"Python", "SQL"}, load_skills())
    assert gaps[0] == {"skill": "AWS", "jobs": 3, "percent": 100}
    assert gaps[1] == {"skill": "Spark", "jobs": 1, "percent": 33}


def test_skills_you_have_are_never_gaps():
    gaps = skill_gaps(JDS, {"Python", "SQL", "AWS", "Spark"}, load_skills())
    assert gaps == []