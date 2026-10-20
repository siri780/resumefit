import subprocess

import streamlit as st

from app.ats import ROOT, latex_to_text, score
from app.build_pdf import OUTPUT, build_pdf
from app.ui import CSS, card, chips, hero, score_color, score_ring

st.set_page_config(page_title="ResumeFit", page_icon="📄", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(hero("📄 ResumeFit",
                 "Paste a job description. Get your ATS match, skill gaps "
                 "and a ready-to-send resume."),
            unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Your profile")
    st.write("**Shirisha Gajendra**")
    st.caption("MS Data Science · Stony Brook University · May 2027")
    st.divider()
    target = st.slider("Target ATS score (%)", 70, 100, 90, step=5)
    st.caption("Apply when your score reaches this target.")

jd = st.text_area("Job description", height=220,
                  placeholder="Paste the full job posting here...")

if st.button("Analyze match", type="primary", width="stretch"):
    if not jd.strip():
        st.warning("Please paste a job description first.")
    else:
        tex = (ROOT / "data" / "resume.tex").read_text(encoding="utf-8")
        st.session_state["result"] = score(latex_to_text(tex), jd)


def preview_image(pdf_path):
    """Turn page 1 of the PDF into a PNG image for the preview tab."""
    out = OUTPUT / "preview"
    subprocess.run(["pdftoppm", "-png", "-r", "90", "-singlefile",
                    str(pdf_path), str(out)], check=True)
    return out.with_suffix(".png")


if "result" in st.session_state:
    result = st.session_state["result"]
    pct = result["percent"]
    color = score_color(pct, target)
    if pct >= target:
        verdict = "✅ Ready"
    elif pct >= 70:
        verdict = "🟡 Tailor"
    else:
        verdict = "🔴 Gaps"

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(score_ring(pct, color), unsafe_allow_html=True)
    c2.markdown(card("Matched skills", len(result["matched"])),
                unsafe_allow_html=True)
    c3.markdown(card("Missing skills", len(result["missing"])),
                unsafe_allow_html=True)
    c4.markdown(card("Verdict", verdict), unsafe_allow_html=True)

    st.write("")
    pdf_path = build_pdf()
    tab1, tab2, tab3 = st.tabs(["🧩 Skills", "📄 Resume preview", "⬇️ Download"])
    with tab1:
        st.markdown("**Matched**")
        st.markdown(chips(result["matched"], "ok"), unsafe_allow_html=True)
        st.markdown("**Missing**")
        st.markdown(chips(result["missing"], "miss"), unsafe_allow_html=True)
    with tab2:
        st.image(str(preview_image(pdf_path)))
    with tab3:
        st.download_button("⬇️ Download resume (PDF)",
                           data=pdf_path.read_bytes(),
                           file_name=pdf_path.name,
                           mime="application/pdf", type="primary")