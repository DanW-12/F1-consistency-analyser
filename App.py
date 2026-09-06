"""
F1 Lap Time Consistency Analyser — Streamlit GUI
==================================================
Wraps consistency_analyser.py in a simple web UI: pick a year, event,
session and driver, and see stint-by-stint consistency stats + plot.

Run with:
    streamlit run app.py
"""

import os

import fastf1
import streamlit as st

from consistency_analyser import stint_consistency, plot_consistency

# --- Setup --------------------------------------------------------------
st.set_page_config(page_title="F1 Lap Time Consistency Analyser", layout="wide")

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

st.title("F1 Lap Time Consistency Analyser")
st.caption("Pick a race and driver to see how consistent their lap times were, stint by stint.")


# --- Cached data loaders --------------------------------------------------
# st.cache_data: for plain serialisable data (the schedule table).
# st.cache_resource: for the FastF1 Session object itself, which holds
# non-serialisable internal state and shouldn't be copied/hashed like data.

@st.cache_data(show_spinner=False)
def get_schedule(year: int):
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    return schedule[["RoundNumber", "EventName"]].reset_index(drop=True)


@st.cache_resource(show_spinner="Loading session data (first load can take a minute)...")
def load_session(year: int, event_name: str, session_type: str):
    session = fastf1.get_session(year, event_name, session_type)
    session.load()
    return session


# --- Sidebar: session selection -------------------------------------------
with st.sidebar:
    st.header("Session")
    year = st.selectbox("Year", list(range(2024, 2017, -1)))
    schedule = get_schedule(year)
    event_name = st.selectbox("Event", schedule["EventName"].tolist())
    session_type = st.selectbox(
        "Session type", ["R", "Q", "Sprint", "FP1", "FP2", "FP3"],
        help="R = Race, Q = Qualifying, Sprint = Sprint race",
    )
    load_clicked = st.button("Load session", type="primary", use_container_width=True)

if "session" not in st.session_state:
    st.session_state.session = None
    st.session_state.session_key = None

session_key = (year, event_name, session_type)

if load_clicked:
    st.session_state.session = load_session(*session_key)
    st.session_state.session_key = session_key

session = st.session_state.session

if session is None or st.session_state.session_key != session_key:
    st.info("Choose a year, event and session in the sidebar, then click **Load session**.")
    st.stop()


# --- Driver selection + analysis ------------------------------------------
drivers = sorted(session.laps["Driver"].unique())
driver = st.selectbox("Driver", drivers)

laps = (
    session.laps.pick_drivers(driver)
    .pick_quicklaps()
    .pick_accurate()
    .reset_index(drop=True)
)

if laps.empty:
    st.warning(f"No clean laps found for {driver} in this session — try another session or driver.")
    st.stop()

laps["LapTime(s)"] = laps["LapTime"].dt.total_seconds()
summary = stint_consistency(laps)

st.subheader(f"{driver} \u2014 {year} {event_name} ({session_type})")

col1, col2 = st.columns([2, 1])
with col1:
    fig = plot_consistency(session, laps, summary, driver, year, event_name)
    st.pyplot(fig)
with col2:
    st.markdown("**Stint consistency summary**")
    st.dataframe(summary, use_container_width=True, hide_index=True)
    st.caption(
        "CV% = std dev / mean lap time. Lower = more consistent. "
        "Comparable across stints run at different absolute paces."
    )