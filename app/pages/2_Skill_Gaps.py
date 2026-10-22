import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # noqa
import altair as alt
import pandas as pd
import streamlit as st

from app.ats import find_skills, latex_to_text, load_skills
from app.bases import BASES, load_base
from app.skill_gaps import load_plan, saved_job_descriptions, skill_gaps
from app.tailor import load_approved
from app.ui import CSS, card, hero, require_password

st.set_page_config(page_title="Skill Gaps · ResumeFit", page_icon="🧭",
                   layout="wide")
require_password()
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(hero("🧭 Skill Gaps",
                 "Skills your target jobs ask for that your resume doesn't "
                 "have yet, and how to earn them."),
            unsafe_allow_html=True)

skills = load_skills()
base = st.selectbox("Compare against base resume", list(BASES))
tex = load_base(base)
have = find_skills(latex_to_text(tex), skills) | load_approved()

jds = saved_job_descriptions()
extra = st.text_area("Optional: paste more job descriptions "
                     "(separate each one with a line containing ---)",
                     height=120)
jds += [j for j in extra.split("---") if j.strip()]

if not jds:
    st.info("Save some applications, or paste job descriptions above, "
            "to see your skill gaps.")
    st.stop()

gaps = skill_gaps(jds, have, skills)
plan = load_plan()

c1, c2, c3 = st.columns(3)
c1.markdown(card("Jobs analyzed", len(jds)), unsafe_allow_html=True)
c2.markdown(card("Skills missing", len(gaps)), unsafe_allow_html=True)
c3.markdown(card("Learn next", gaps[0]["skill"] if gaps else "None 🎉"),
            unsafe_allow_html=True)

if not gaps:
    st.success("Your resume covers every skill these jobs ask for.")
    st.stop()

df = pd.DataFrame(gaps)
df["project"] = df["skill"].map(
    lambda s: plan.get(s, ("Add a project for this in skill_plan.csv", 0))[0])
df["days"] = df["skill"].map(lambda s: plan.get(s, ("", 0))[1])

st.write("")
st.subheader("Most-requested missing skills")
chart = (
    alt.Chart(df.head(10))
    .mark_bar(color="#4F46E5", cornerRadiusEnd=4, size=18)
    .encode(
        x=alt.X("percent:Q", title="% of jobs asking for it"),
        y=alt.Y("skill:N", sort="-x", title=None),
        tooltip=[alt.Tooltip("skill:N", title="Skill"),
                 alt.Tooltip("jobs:Q", title="Jobs"),
                 alt.Tooltip("percent:Q", title="% of jobs")],
    )
)
st.altair_chart(chart, width="stretch")

st.subheader("Your learning plan")
top5_days = int(df.head(5)["days"].sum())
st.caption(f"Closing your top 5 gaps takes about {top5_days} days of projects.")
st.dataframe(
    df.rename(columns={"skill": "Skill", "jobs": "Jobs", "percent": "% of jobs",
                       "project": "Proof project", "days": "Days"}),
    hide_index=True, width="stretch",
)