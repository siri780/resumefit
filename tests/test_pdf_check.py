import pytest

from app.ats import latex_to_text
from app.bases import BASES, load_base
from app.build_pdf import build_pdf
from app.pdf_check import check_pdf


@pytest.mark.parametrize("name", list(BASES))
def test_each_base_resume_pdf_passes_all_checks(name):
    tex = load_base(name)
    pdf = build_pdf("test_" + name.replace(" ", "_"), tex=tex)
    assert check_pdf(pdf, latex_to_text(tex)) == []


def test_flags_word_missing_from_pdf():
    pdf = build_pdf("test_resume")
    problems = check_pdf(pdf, "A made-up word: zzfirefly")
    assert any("broken" in p for p in problems)
