import pandas as pd
import streamlit as st

from app.applications import FIELDS, STATUSES, read_tracker, write_tracker
from app.ui import CSS, card, hero

st.set_page_config(page_title="Tracker · ResumeFit", page_icon="📋",
                   layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(hero("📋 Application Tracker",
                 "Every application you've saved, in one place."),
            unsafe_allow_html=True)

rows = read_tracker()
if not rows:
    st.info("No applications saved yet. Tailor a resume on the main page "
            "and click 💾 Save application.")
    st.stop()

df = pd.DataFrame(rows, columns=FIELDS)

# ---------- Summary cards ----------
total = len(df)
interviews = int((df["status"] == "Interview").sum())
offers = int((df["status"] == "Offer").sum())
responses = interviews + offers
rate = round(100 * responses / total) if total else 0

c1, c2, c3, c4 = st.columns(4)
c1.markdown(card("Applications", total), unsafe_allow_html=True)
c2.markdown(card("Interviews", interviews), unsafe_allow_html=True)
c3.markdown(card("Offers", offers), unsafe_allow_html=True)
c4.markdown(card("Response rate", f"{rate}%"), unsafe_allow_html=True)

st.write("")

# ---------- Filter + editable table ----------
shown = st.multiselect("Filter by status", STATUSES, default=STATUSES)
view = df[df["status"].isin(shown)]

edited = st.data_editor(
    view,
    column_config={
        "status": st.column_config.SelectboxColumn(
            "Status", options=STATUSES, required=True),
        "link": st.column_config.LinkColumn("Link"),
        "notes": st.column_config.TextColumn("Notes"),
    },
    disabled=["date", "company", "role", "ats_before", "ats_after", "folder"],
    hide_index=True,
    width="stretch",
)

if st.button("💾 Save changes", type="primary"):
    df.update(edited)
    write_tracker(df.to_dict("records"))
    st.success("Tracker updated.")