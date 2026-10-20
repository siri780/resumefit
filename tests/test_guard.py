from app.ats import load_skills
from app.guard import check_bullet, check_latex, check_numbers, numbers_in

ORIGINAL = "Automated SQL ETL pipelines that reduced manual reporting workload by 40\\%."
RESUME_SKILLS = {"SQL", "ETL", "Python"}


def test_numbers_with_commas_and_decimals():
    assert numbers_in("5,863 images, 92.07% accuracy") == {"5863", "92.07"}


def test_blocks_changed_number():
    problems = check_numbers(ORIGINAL, "Cut reporting work by 60\\%.")
    assert any("60" in p for p in problems)


def test_blocks_new_skill():
    new = "Automated SQL ETL pipelines on AWS, reducing manual work by 40\\%."
    problems = check_bullet(ORIGINAL, new, RESUME_SKILLS, load_skills())
    assert any("AWS" in p for p in problems)


def test_blocks_unescaped_percent():
    assert check_latex("reduced workload by 40%.") != []
    assert check_latex("reduced workload by 40\\%.") == []


def test_safe_rewording_passes():
    new = "Built automated SQL ETL pipelines, cutting manual reporting effort by 40\\%."
    assert check_bullet(ORIGINAL, new, RESUME_SKILLS, load_skills()) == []