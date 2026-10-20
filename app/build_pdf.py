from pathlib import Path
import os
import subprocess
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"

load_dotenv(ROOT / ".env")


def fill_placeholders(tex):
    phone = os.getenv("PHONE")
    email = os.getenv("EMAIL")
    if not phone or not email:
        raise ValueError("PHONE or EMAIL is missing in .env")
    return tex.replace("{{PHONE}}", phone).replace("{{EMAIL}}", email)


def build_pdf(out_name="Shirisha_Gajendra_Resume"):
    OUTPUT.mkdir(exist_ok=True)
    tex = (DATA / "resume.tex").read_text(encoding="utf-8")
    tex = fill_placeholders(tex)
    tex_path = OUTPUT / f"{out_name}.tex"
    tex_path.write_text(tex, encoding="utf-8")

    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode",
         "-output-directory", str(OUTPUT), str(tex_path)],
        capture_output=True, text=True,
    )

    pdf_path = OUTPUT / f"{out_name}.pdf"
    if not pdf_path.exists():
        print(result.stdout[-2000:])
        raise RuntimeError("PDF was not created")
    return pdf_path


if __name__ == "__main__":
    print("Created:", build_pdf())