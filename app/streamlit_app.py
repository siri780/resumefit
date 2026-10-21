import re
import subprocess

import streamlit as st

from app.applications import already_applied, save_application
from app.ats import ROOT, find_skills, latex_to_text, load_skills, score
from app.backup import backup
from app.build_pdf import OUTPUT, build_pdf
from app.latex_io import apply_edits, get_bullets
from app.pdf_check import check_pdf
from app.tailor import load_approved, save_approved, tailor
from app.ui import CSS, card, chips, hero, score_color, score_ring

RESUME = ROOT / "data" / "resume.tex"

st.set_page_config(page_title="ResumeFit", page_icon="📄", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(hero("📄 ResumeFit",
                 "Paste a job description. Get your ATS match, honest AI "
                 "edits and a ready-to-send resume."),
            unsafe_allow_html=True)

skills = load_skills()
tex = RESUME.read_text(encoding="utf-8")
resume_skills = find_skills(latex_to_text(tex), skills)


def readable(text):
    """Show LaTeX bullet text without backslashes."""
    return text.replace("\\%", "%").replace("\\&", "&")


def safe_name(text):
    """Turn a company name into a safe file name part."""
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_") or "Tailored"


def preview_image(pdf_path):
    """Turn page 1 of the PDF into a PNG image."""
    out = OUTPUT / f"{pdf_path.stem}_preview"
    subprocess.run(["pdftoppm", "-png", "-r", "90", "-singlefile",
                    str(pdf_path), str(out)], check=True)
    return out.with_suffix(".png")


# ---------- Sidebar ----------
with st.sidebar:
    st.subheader("Your profile")
    st.write("**Shirisha Gajendra**")
    st.caption("MS Data Science · Stony Brook University · May 2027")
    st.divider()
    target = st.slider("Target ATS score (%)", 70, 100, 90, step=5)
    st.divider()
    st.subheader("Approved extra skills")
    st.caption("Only skills you can honestly explain in an interview. "
               "The AI may use these; anything else is blocked.")
    options = sorted(s["skill"] for s in skills
                     if s["skill"] not in resume_skills)
    approved = st.multiselect("Approved skills", options,
                              default=sorted(load_approved() & set(options)),
                              label_visibility="collapsed")
    if set(approved) != load_approved():
        save_approved(approved)

# ---------- Input ----------
col_a, col_b = st.columns(2)
company = col_a.text_input("Company", placeholder="e.g. Pinterest")
role = col_b.text_input("Role", placeholder="e.g. Data Scientist")
link = st.text_input("Job link (optional)", placeholder="https://...")
jd = st.text_area("Job description", height=220,
                  placeholder="Paste the full job posting here...")

if company.strip() and role.strip() and already_applied(company, role):
    st.warning(f"⚠️ You already saved an application for "
               f"{company} – {role}.")

if st.button("Analyze match", type="primary", width="stretch"):
    if not jd.strip():
        st.warning("Please paste a job description first.")
    else:
        st.session_state["result"] = score(latex_to_text(tex), jd, skills)
        st.session_state["jd"] = jd
        st.session_state.pop("suggestions", None)
        st.session_state.pop("tailored", None)

# ---------- Results ----------
if "result" in st.session_state:
    result = st.session_state["result"]
    pct = result["percent"]
    if pct >= target:
        verdict = "✅ Ready"
    elif pct >= 70:
        verdict = "🟡 Tailor"
    else:
        verdict = "🔴 Gaps"

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(score_ring(pct, score_color(pct, target)),
                unsafe_allow_html=True)
    c2.markdown(card("Matched skills", len(result["matched"])),
                unsafe_allow_html=True)
    c3.markdown(card("Missing skills", len(result["missing"])),
                unsafe_allow_html=True)
    c4.markdown(card("Verdict", verdict), unsafe_allow_html=True)

    st.write("")
    tab1, tab2 = st.tabs(["🧩 Skills", "✨ Tailor with AI"])

    with tab1:
        st.markdown("**Matched**")
        st.markdown(chips(result["matched"], "ok"), unsafe_allow_html=True)
        st.markdown("**Missing**")
        st.markdown(chips(result["missing"], "miss"), unsafe_allow_html=True)

    with tab2:
        if st.button("✨ Get AI suggestions"):
            with st.spinner("Asking the AI and checking every suggestion..."):
                st.session_state["suggestions"] = tailor(
                    get_bullets(tex), st.session_state["jd"],
                    resume_skills, skills, result["missing"])
            st.session_state.pop("tailored", None)

        suggestions = st.session_state.get("suggestions")
        if suggestions == []:
            st.info("No honest improvements found for this job.")

        if suggestions:
            chosen = {}
            for s in suggestions:
                with st.container(border=True):
                    st.caption(f"Bullet {s['id']} · {s['reason']}")
                    st.markdown(f"**Before:** {readable(s['original'])}")
                    st.markdown(f"**After:** {readable(s['new'])}")
                    if s["problems"]:
                        for p in s["problems"]:
                            st.error(p)
                        st.caption("🚫 Blocked by the guard")
                    elif st.checkbox("Use this edit", value=True,
                                     key=f"use_{s['id']}"):
                        chosen[s["id"]] = s["new"]

            if st.button("🛠️ Build tailored resume", type="primary",
                         disabled=not chosen):
                new_tex = apply_edits(tex, chosen)
                after = score(latex_to_text(new_tex),
                              st.session_state["jd"], skills)
                name = f"Shirisha_Gajendra_{safe_name(company)}"
                pdf = build_pdf(name, tex=new_tex)
                st.session_state["tailored"] = {
                    "pdf": pdf,
                    "tex": new_tex,
                    "after": after,
                    "checks": check_pdf(pdf, latex_to_text(new_tex)),
                }

        tailored = st.session_state.get("tailored")
        if tailored:
            after_pct = tailored["after"]["percent"]
            st.metric("ATS score after tailoring", f"{after_pct}%",
                      delta=f"{after_pct - pct} points")
            pdf = tailored["pdf"]
            if tailored["checks"]:
                for problem in tailored["checks"]:
                    st.error(f"⚠️ {problem}")
            else:
                st.success("✅ 1 page · details filled in · readable by ATS")

            b1, b2 = st.columns(2)
            b1.download_button("⬇️ Download tailored resume (PDF)",
                               data=pdf.read_bytes(), file_name=pdf.name,
                               mime="application/pdf", type="primary",
                               width="stretch")
            if b2.button("💾 Save application", width="stretch",
                         disabled=not (company.strip() and role.strip())):
                folder = save_application(company, role,
                                          st.session_state["jd"],
                                          tailored["tex"], pdf, result,
                                          tailored["after"], link)
                st.success(f"Saved to applications/{folder.name}")
                ok, message = backup(f"Add {company} - {role}")
                st.success(message) if ok else st.warning(message)
            st.image(str(preview_image(pdf)))