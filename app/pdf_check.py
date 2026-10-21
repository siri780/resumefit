import re

import pdfplumber


def check_pdf(pdf_path, source_text):
    """Return a list of problems with the finished PDF. Empty = safe."""
    problems = []
    with pdfplumber.open(pdf_path) as pdf:
        pages = len(pdf.pages)
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if pages != 1:
        problems.append(f"Resume is {pages} pages (must be 1)")

    if "{{" in text:
        problems.append("A private placeholder was not filled in")

    flat = text.replace("\n", " ")
    words = set(re.findall(r"[A-Za-z]*f[il][A-Za-z]*", source_text))
    broken = sorted(w for w in words if w not in flat)
    if broken:
        problems.append("Text may be broken in PDF: " + ", ".join(broken[:5]))

    return problems