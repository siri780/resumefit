from app.ats import latex_to_text
from app.build_pdf import build_pdf
from app.latex_io import RESUME
from app.pdf_check import check_pdf


def test_base_resume_pdf_passes_all_checks():
    pdf = build_pdf("test_resume")
    source = latex_to_text(RESUME.read_text(encoding="utf-8"))
    assert check_pdf(pdf, source) == []


def test_flags_word_missing_from_pdf():
    pdf = build_pdf("test_resume")
    problems = check_pdf(pdf, "A made-up word: zzfirefly")
    assert any("broken" in p for p in problems)