"""
app.py
"""

from __future__ import annotations

from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st

from extractor import (
    extract_action_items,
    extract_key_topics,
    extract_participants,
    generate_summary,
)
from utils import (
    SAMPLE_NOTES,
    build_insights,
    format_checklist_csv,
    format_checklist_ics,
    format_checklist_md,
    format_checklist_txt,
    items_to_dataframe,
    summary_stats,
)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NoteCraft — Meeting Notes → Action Items",
    page_icon=":material/check_circle:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark product theme: quiet charcoal surfaces, readable type, and one restrained
# teal accent. Custom CSS is limited to details Streamlit's theme tokens cannot
# currently control, such as the hero treatment and data-editor framing.
_CUSTOM_CSS = """
<style>
/* ---------- Product palette ---------- */
:root {
    --nc-bg: #111315;
    --nc-surface: #181b1f;
    --nc-surface-raised: #20252a;
    --nc-border: #30363d;
    --nc-border-strong: #46505a;
    --nc-text: #e7ebef;
    --nc-muted: #9aa4af;
    --nc-accent: #55b7a6;
    --nc-accent-soft: #18312f;
    --nc-warning: #d6a85f;
    --nc-danger: #d97878;
    --nc-success: #69b58d;
}

/* ---------- Base and typography ---------- */
.stApp, .stApp > header {
    background: var(--nc-bg);
    color: var(--nc-text);
}
.stApp {
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}
h1, h2, h3, h4, h5, h6,
.stMetricLabel, .stMetricValue {
    color: var(--nc-text) !important;
    letter-spacing: 0 !important;
}
p, label, [data-testid="stCaptionContainer"] {
    color: var(--nc-muted);
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #15181b;
    border-right: 1px solid var(--nc-border);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--nc-text) !important;
    font-size: 0.95rem !important;
    font-weight: 650 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: var(--nc-border);
}

/* ---------- Hero and section rhythm ---------- */
.notecraft-hero {
    background: var(--nc-surface);
    border: 1px solid var(--nc-border);
    border-left: 3px solid var(--nc-accent);
    border-radius: 6px;
    padding: 22px 26px;
    margin-bottom: 22px;
}
.notecraft-hero h1 {
    color: var(--nc-text) !important;
    font-size: 2.15rem !important;
    font-weight: 700 !important;
    line-height: 1.1 !important;
    margin-bottom: 7px !important;
}
.notecraft-hero .subtitle {
    color: var(--nc-muted);
    font-size: 0.92rem;
    margin-bottom: 15px;
}
.notecraft-hero .badges {
    display: flex;
    gap: 7px;
    flex-wrap: wrap;
}
.notecraft-hero .badge {
    display: inline-flex;
    align-items: center;
    background: var(--nc-surface-raised);
    border: 1px solid var(--nc-border);
    color: var(--nc-muted);
    padding: 4px 9px;
    border-radius: 4px;
    font-size: 0.74rem;
    font-weight: 600;
}
.notecraft-hero .badge:first-child {
    color: var(--nc-accent);
    border-color: #2b625a;
}
.notecraft-hero .badge.alt,
.notecraft-hero .badge.alt2 {
    color: var(--nc-muted);
    background: var(--nc-surface-raised);
    border-color: var(--nc-border);
}
.section-divider {
    height: 1px;
    background: var(--nc-border);
    margin: 22px 0;
}

/* ---------- Metrics ---------- */
.stMetric {
    background: var(--nc-surface);
    border: 1px solid var(--nc-border);
    border-radius: 6px;
    padding: 13px 16px !important;
}
.stMetricLabel {
    color: var(--nc-muted) !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
}
.stMetricValue {
    color: var(--nc-accent) !important;
    font-weight: 700 !important;
}

/* ---------- Controls ---------- */
.stButton > button,
.stDownloadButton > button {
    min-height: 38px;
    border-radius: 5px !important;
    border: 1px solid var(--nc-border-strong) !important;
    background: var(--nc-surface-raised) !important;
    color: var(--nc-text) !important;
    font-weight: 600 !important;
    transition: border-color 120ms ease, background-color 120ms ease !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: var(--nc-accent) !important;
    background: #26302f !important;
    color: var(--nc-text) !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--nc-accent) !important;
    border-color: var(--nc-accent) !important;
    color: #10201d !important;
}
.stButton > button[kind="primary"] *,
.stButton > button[data-testid="stBaseButton-primary"] * {
    color: #10201d !important;
    fill: #10201d !important;
}
.stButton > button[kind="primary"] p,
.stButton > button[data-testid="stBaseButton-primary"] p {
    font-weight: 700 !important;
}
.stButton > button span[class*="material-symbols"],
.stDownloadButton > button span[class*="material-symbols"] {
    color: var(--nc-accent) !important;
    fill: var(--nc-accent) !important;
    font-variation-settings: "FILL" 1, "wght" 600, "GRAD" 0, "opsz" 20;
}
.stButton > button[kind="primary"] span[class*="material-symbols"],
.stButton > button[data-testid="stBaseButton-primary"] span[class*="material-symbols"] {
    color: #10201d !important;
    fill: #10201d !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: #6ac7b5 !important;
    border-color: #6ac7b5 !important;
}
.stTextArea > div > div,
.stTextInput > div > div,
.stSelectbox > div > div > div,
[data-baseweb="select"] > div {
    background: var(--nc-surface) !important;
    border: 1px solid var(--nc-border) !important;
    border-radius: 5px !important;
    color: var(--nc-text) !important;
}
.stTextArea > div > div:focus-within,
.stTextInput > div > div:focus-within,
[data-baseweb="select"]:focus-within {
    border-color: var(--nc-accent) !important;
    box-shadow: 0 0 0 1px var(--nc-accent) !important;
}
input, textarea {
    color: var(--nc-text) !important;
}
.stMarkdown h3 span[class*="material-symbols"],
.stMarkdown h4 span[class*="material-symbols"],
.stExpander span[class*="material-symbols"] {
    color: var(--nc-accent) !important;
    fill: var(--nc-accent) !important;
    font-variation-settings: "FILL" 1, "wght" 600, "GRAD" 0, "opsz" 20;
}
.stTabs [data-baseweb="tab"] span[class*="material-symbols"] {
    color: var(--nc-muted) !important;
    fill: var(--nc-muted) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] span[class*="material-symbols"] {
    color: var(--nc-accent) !important;
    fill: var(--nc-accent) !important;
}
.stTabs [data-baseweb="tab"]:nth-child(1) span[class*="material-symbols"] {
    color: #62c2b0 !important;
    fill: #62c2b0 !important;
}
.stTabs [data-baseweb="tab"]:nth-child(2) span[class*="material-symbols"] {
    color: #79a9e8 !important;
    fill: #79a9e8 !important;
}
.stTabs [data-baseweb="tab"]:nth-child(3) span[class*="material-symbols"] {
    color: #d6ad6b !important;
    fill: #d6ad6b !important;
}
.stTabs [data-baseweb="tab"]:nth-child(4) span[class*="material-symbols"] {
    color: #79c59b !important;
    fill: #79c59b !important;
}
.stTabs [data-baseweb="tab"]:nth-child(5) span[class*="material-symbols"] {
    color: #c8a36b !important;
    fill: #c8a36b !important;
}
.stTabs [data-baseweb="tab"]:nth-child(6) span[class*="material-symbols"] {
    color: #d47f83 !important;
    fill: #d47f83 !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"]:nth-child(1) span[class*="material-symbols"] {
    color: #75d8c4 !important;
    fill: #75d8c4 !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"]:nth-child(2) span[class*="material-symbols"] {
    color: #91bdf2 !important;
    fill: #91bdf2 !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"]:nth-child(3) span[class*="material-symbols"] {
    color: #e6c27e !important;
    fill: #e6c27e !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"]:nth-child(4) span[class*="material-symbols"] {
    color: #8bd5aa !important;
    fill: #8bd5aa !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"]:nth-child(5) span[class*="material-symbols"] {
    color: #e0bd7c !important;
    fill: #e0bd7c !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"]:nth-child(6) span[class*="material-symbols"] {
    color: #e89498 !important;
    fill: #e89498 !important;
}
/* Streamlit renders Material Symbols as image icons in the browser. Filters
   provide reliable color treatment across the current Streamlit renderer. */
img[alt="checklist icon"] { filter: invert(71%) sepia(30%) saturate(650%) hue-rotate(121deg) brightness(88%) contrast(88%); }
img[alt="analytics icon"] { filter: invert(68%) sepia(32%) saturate(850%) hue-rotate(181deg) brightness(94%) contrast(91%); }
img[alt="description icon"] { filter: invert(75%) sepia(38%) saturate(620%) hue-rotate(355deg) brightness(93%) contrast(89%); }
img[alt="group icon"] { filter: invert(70%) sepia(27%) saturate(720%) hue-rotate(91deg) brightness(92%) contrast(89%); }
img[alt="label icon"] { filter: invert(71%) sepia(34%) saturate(650%) hue-rotate(354deg) brightness(92%) contrast(88%); }
img[alt="help icon"] { filter: invert(62%) sepia(32%) saturate(800%) hue-rotate(315deg) brightness(94%) contrast(88%); }
img[alt="settings icon"],
img[alt="playlist_add icon"],
img[alt="info icon"],
img[alt="edit_note icon"] { filter: invert(72%) sepia(29%) saturate(650%) hue-rotate(121deg) brightness(90%) contrast(88%); }
img[alt="bolt icon"] { filter: invert(14%) sepia(14%) saturate(920%) hue-rotate(117deg) brightness(77%) contrast(92%); }
img[alt="delete icon"] { filter: invert(62%) sepia(35%) saturate(850%) hue-rotate(310deg) brightness(90%) contrast(88%); }
img[alt="calendar_month icon"] { filter: invert(72%) sepia(38%) saturate(760%) hue-rotate(354deg) brightness(94%) contrast(90%); }
img[alt="download icon"] { filter: invert(71%) sepia(30%) saturate(650%) hue-rotate(121deg) brightness(88%) contrast(88%); }
/* Streamlit's tab renderer uses ARIA-labeled Material Symbol spans. */
span[role="img"][aria-label="checklist icon"] { color: #75d8c4 !important; }
span[role="img"][aria-label="analytics icon"] { color: #91bdf2 !important; }
span[role="img"][aria-label="description icon"] { color: #e6c27e !important; }
span[role="img"][aria-label="group icon"] { color: #8bd5aa !important; }
span[role="img"][aria-label="label icon"] { color: #e0bd7c !important; }
span[role="img"][aria-label="help icon"] { color: #e89498 !important; }
span[role="img"][aria-label="settings icon"],
span[role="img"][aria-label="playlist_add icon"],
span[role="img"][aria-label="info icon"],
span[role="img"][aria-label="edit_note icon"] { color: #75d8c4 !important; }
span[role="img"][aria-label="bolt icon"] { color: #10201d !important; }
span[role="img"][aria-label="delete icon"] { color: #e89498 !important; }
span[role="img"][aria-label="calendar_month icon"] { color: #e0bd7c !important; }
span[role="img"][aria-label="download icon"] { color: #75d8c4 !important; }

/* ---------- Notes input area ---------- */
.notes-input-shell {
    background: var(--nc-surface);
    border: 1px solid var(--nc-border);
    border-radius: 6px;
    padding: 16px;
    margin: 8px 0 14px;
}
.notes-input-shell h4 {
    color: var(--nc-text) !important;
    font-size: 0.86rem !important;
    font-weight: 650 !important;
    margin: 0 0 3px !important;
}
.notes-input-shell .input-hint {
    color: var(--nc-muted);
    font-size: 0.77rem;
    margin-bottom: 10px;
}
[data-testid="stFileUploader"] {
    background: var(--nc-surface-raised);
    border: 1px dashed var(--nc-border-strong);
    border-radius: 5px;
    padding: 8px;
}
[data-testid="stFileUploader"] section {
    padding: 8px 10px;
    border: 0;
    background: transparent;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: var(--nc-muted) !important;
}
[data-testid="stFileUploader"] button {
    color: var(--nc-text) !important;
    border-color: var(--nc-border-strong) !important;
    background: var(--nc-surface) !important;
}
.notes-input-shell .stTextArea textarea {
    min-height: 174px;
    line-height: 1.5;
}

/* ---------- Data and navigation ---------- */
.stDataFrame, [data-testid="stDataFrame"] {
    border: 1px solid var(--nc-border);
    border-radius: 6px;
    overflow: hidden;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: var(--nc-surface);
    border-bottom: 1px solid var(--nc-border);
}
.stTabs [data-baseweb="tab"] {
    color: var(--nc-muted) !important;
    padding: 9px 14px !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--nc-accent) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--nc-accent) !important;
}
.streamlit-expanderHeader {
    background: var(--nc-surface);
    border: 1px solid var(--nc-border);
    border-radius: 5px;
    color: var(--nc-text) !important;
    font-weight: 600 !important;
}

/* ---------- Status and helper surfaces ---------- */
.status-pill {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.74rem;
    font-weight: 600;
}
.status-pill.success { background: #193126; color: var(--nc-success); border: 1px solid #315b45; }
.status-pill.warn { background: #342b1d; color: var(--nc-warning); border: 1px solid #66512f; }
.status-pill.danger { background: #382326; color: var(--nc-danger); border: 1px solid #6b3a3f; }
.status-pill.info { background: var(--nc-accent-soft); color: var(--nc-accent); border: 1px solid #2b625a; }
.muted { color: var(--nc-muted); font-size: 0.85rem; }
.mono { font-family: "JetBrains Mono", Consolas, monospace; font-size: 0.82rem; }
.callout {
    background: var(--nc-surface);
    border: 1px solid var(--nc-border);
    border-left: 3px solid var(--nc-accent);
    padding: 12px 16px;
    border-radius: 5px;
    margin: 12px 0;
    color: var(--nc-text);
}
.callout.warn { border-left-color: var(--nc-warning); }
.callout.danger { border-left-color: var(--nc-danger); }
.callout.success { border-left-color: var(--nc-success); }
</style>
"""

st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "results_df" not in st.session_state:
    st.session_state.results_df = None
if "notes_text" not in st.session_state:
    st.session_state.notes_text = ""
if "item_lookup" not in st.session_state:
    st.session_state.item_lookup = {}
if "summary_text" not in st.session_state:
    st.session_state.summary_text = ""
if "participants" not in st.session_state:
    st.session_state.participants = []
if "key_topics" not in st.session_state:
    st.session_state.key_topics = []


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### :material/settings: Settings")

    meeting_date = st.date_input(
        "Meeting date",
        value=date.today(),
        help="Used as the reference point for resolving relative dates like 'next Friday' or 'in two weeks'.",
    )

    st.markdown("---")
    st.markdown("### :material/playlist_add: Try a sample")
    sample_choice = st.selectbox("Sample notes", ["(none)"] + list(SAMPLE_NOTES.keys()))
    if st.button("Load Sample Notes", width='stretch', type="primary"):
        if sample_choice != "(none)":
            st.session_state.notes_text = SAMPLE_NOTES[sample_choice]
            st.session_state.results_df = None
            st.session_state.summary_text = ""
            st.session_state.participants = []
            st.session_state.key_topics = []
            st.toast(f"Loaded sample: {sample_choice}", icon=":material/note_add:")
        else:
            st.warning("Pick a sample from the dropdown first.")

    st.markdown("---")
    with st.expander(":material/info: How it works"):
        st.markdown(
            """
NoteCraft uses **rule-based NLP** (spaCy) — no LLMs, no paid APIs, and
nothing leaves your machine.

For every sentence in your notes, it checks for:
- **Modal/obligation verbs** — "will", "need to", "should", "must"...
- **Imperative mood** — sentences that start with a command verb, like
  "Send the report..."
- **Task-signaling verbs** — "review", "schedule", "follow up"...
- **Assignment phrasing** — "Priya will...", "assigned to Sam"...

Sentences matching one or more of these get flagged as action items.
Owners are found via named-entity recognition (looking for people's
names), and deadlines via date entities + a few regex fallbacks for
phrases like "next week" or "EOD".

**New in this revision:**
- Priority score (confidence + deadline urgency + owner)
- Extractive meeting summary
- Participants list (NER)
- Key topics (noun chunks)
- Per-item sentiment (lexicon-based)
- Stats dashboard
- .ics calendar export
            """
        )

    st.markdown("---")
    st.caption("NoteCraft · v2.0 · Focused dark workspace")


# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------
st.markdown(
    """
<div class="notecraft-hero">
        <h1>NoteCraft</h1>
        <div class="subtitle">Meeting Notes → Action Items Extractor · rule-based NLP · 100% offline</div>
        <div class="badges">
            <span class="badge">spaCy · en_core_web_sm</span>
            <span class="badge alt">Priority + Sentiment</span>
            <span class="badge alt2">.ics / .txt / .csv export</span>
        </div>
</div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Main area -- Input (always visible at the top)
# ---------------------------------------------------------------------------
st.markdown("#### :material/edit_note: Add meeting notes")
st.caption("Upload a notes file or paste meeting notes directly. Uploaded text appears in the editor for review before extraction.")

with st.container(border=True):
    st.markdown("**Meeting notes input**")
    st.caption("Use the upload control for a file, or paste and edit the extracted text below. Both paths use the same action-item extraction pipeline.")
    upload_col, paste_col = st.columns([1, 3], gap="large")

    with upload_col:
        uploaded_file = st.file_uploader(
            "Upload a .txt file",
            type=["txt"],
            help="UTF-8 plain-text files only.",
        )
        if uploaded_file is not None:
            try:
                decoded = uploaded_file.read().decode("utf-8")
                if decoded != st.session_state.notes_text:
                    st.session_state.notes_text = decoded
                    st.session_state.results_df = None
                    st.session_state.summary_text = ""
                    st.session_state.participants = []
                    st.session_state.key_topics = []
                    st.toast("File loaded", icon=":material/description:")
            except UnicodeDecodeError:
                st.error(
                    "Couldn't read that file because it is not UTF-8 text. "
                    "Paste the content directly instead."
                )

    with paste_col:
        notes_text = st.text_area(
            "Review extracted or pasted notes",
            value=st.session_state.notes_text,
            height=180,
            placeholder="Uploaded text or pasted notes will appear here.\n\nReview the content, then select Extract action items.",
            help="Review or edit the meeting text before running extraction.",
        )
        st.session_state.notes_text = notes_text


extract_col, clear_col, spacer_col = st.columns([1.8, 1.15, 3.05], gap="small")
with extract_col:
    extract_clicked = st.button(":material/bolt: Extract action items", type="primary", width='stretch')
with clear_col:
    if st.button(":material/delete: Clear", width='stretch'):
        st.session_state.notes_text = ""
        st.session_state.results_df = None
        st.session_state.summary_text = ""
        st.session_state.participants = []
        st.session_state.key_topics = []
        st.session_state.item_lookup = {}
        st.rerun()


# ---------------------------------------------------------------------------
# Run extraction
# ---------------------------------------------------------------------------
if extract_clicked:
    if not notes_text or not notes_text.strip():
        st.warning("Paste or upload some notes first.")
    else:
        progress = st.progress(0, text="Running NLP pipeline...")
        progress.progress(20, text="Tokenizing + parsing with spaCy...")
        items = extract_action_items(notes_text, reference_date=meeting_date)
        progress.progress(60, text="Extracting participants + topics...")
        st.session_state.results_df = items_to_dataframe(items)
        st.session_state.item_lookup = {item.id: item for item in items}
        st.session_state.summary_text = generate_summary(notes_text, max_sentences=3)
        st.session_state.participants = extract_participants(notes_text)
        st.session_state.key_topics = extract_key_topics(notes_text, top_k=10)
        progress.progress(100, text="Done.")
        st.toast(f"Extracted {len(items)} action items", icon=":material/check_circle:")
        progress.empty()


# ---------------------------------------------------------------------------
# Results area (tabbed)
# ---------------------------------------------------------------------------
st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

if st.session_state.results_df is None or st.session_state.results_df.empty:
    if st.session_state.results_df is not None and st.session_state.results_df.empty:
        st.info("No action items found in these notes. Try rephrasing, or check the 'How it works' panel for what the tool looks for.")
    else:
        st.markdown(
            """
<div class="callout">
    <strong>Nothing extracted yet.</strong> Upload or paste your meeting notes above (or load a sample from the sidebar), then click <strong>Extract action items</strong> to get started.
</div>
            """,
            unsafe_allow_html=True,
        )
else:
    # The ORIGINAL extracted df is the data_editor's default. We do NOT
    # overwrite st.session_state.results_df with the edited_df — that was
    # the source of the original bug. Streamlit's data_editor preserves
    # the user's checkbox edits via its `key=` param across re-runs.
    df = st.session_state.results_df

    # Summary metrics (top of results area)
    stats = summary_stats(df)
    insights = build_insights(df, reference_date=meeting_date)

    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("Action items", stats["total"])
    metric_col2.metric("With owner", stats["with_owner"])
    metric_col3.metric("With deadline", stats["with_deadline"])
    metric_col4.metric("High priority", insights["priority_counts"]["High"])
    metric_col5.metric("Overdue", insights["deadline_horizon"]["overdue"])

    # Tabs: Checklist | Insights | Summary | Participants | Topics | Why flagged
    tab_checklist, tab_insights, tab_summary, tab_people, tab_topics, tab_why = st.tabs([
        ":material/checklist: Checklist",
        ":material/analytics: Insights",
        ":material/description: Summary",
        ":material/group: Participants",
        ":material/label: Topics",
        ":material/help: Why flagged",
    ])

    # ---------- Tab 1: Checklist (the editable table) ----------
    with tab_checklist:
        st.caption("Toggle the **Include** checkbox to keep / drop a row before exporting. Edits are kept until you re-run extraction.")

        # CRITICAL BUG FIX:
        # - `df` here is st.session_state.results_df (the ORIGINAL extracted df).
        # - We pass it as the default to st.data_editor.
        # - Streamlit tracks user edits internally via key="results_editor".
        # - We use the returned `edited_df` for everything downstream.
        # - We do NOT write `edited_df` back to st.session_state.results_df.
        edited_df = st.data_editor(
            df,
            column_config={
                "Include": st.column_config.CheckboxColumn("Include", default=True, help="Uncheck to exclude this row from exports."),
                "id": None,  # hide internal id column
                "Task": st.column_config.TextColumn("Task", width="large"),
                "Owner": st.column_config.TextColumn("Owner"),
                "Deadline": st.column_config.TextColumn("Deadline (ISO)"),
                "Deadline (raw)": st.column_config.TextColumn("Deadline (raw)"),
                "Confidence": st.column_config.SelectboxColumn(
                    "Confidence", options=["High", "Medium", "Low"], required=True
                ),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority", options=["High", "Medium", "Low"], required=True
                ),
                "Priority Score": st.column_config.NumberColumn(
                    "Score", min_value=1, max_value=5, step=1, help="1 (lowest) — 5 (highest)"
                ),
                "Sentiment": st.column_config.SelectboxColumn(
                    "Sentiment", options=["Positive", "Neutral", "Negative"], required=True
                ),
            },
            hide_index=True,
            width='stretch',
            key="results_editor",
        )

        # Filters (applied to the view, not to the underlying data)
        st.markdown("**Filters**")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            filter_priority = st.multiselect("Priority", ["High", "Medium", "Low"], default=[])
        with f_col2:
            filter_confidence = st.multiselect("Confidence", ["High", "Medium", "Low"], default=[])
        with f_col3:
            filter_sentiment = st.multiselect("Sentiment", ["Positive", "Neutral", "Negative"], default=[])
        with f_col4:
            search_term = st.text_input("Search task text", placeholder="e.g. budget, demo, vendor...")

        # Build a view dataframe (the data_editor's edits are in edited_df;
        # the view is purely for display/export here)
        view_df = edited_df.copy()
        if filter_priority:
            view_df = view_df[view_df["Priority"].isin(filter_priority)]
        if filter_confidence:
            view_df = view_df[view_df["Confidence"].isin(filter_confidence)]
        if filter_sentiment:
            view_df = view_df[view_df["Sentiment"].isin(filter_sentiment)]
        if search_term.strip():
            view_df = view_df[view_df["Task"].str.contains(search_term.strip(), case=False, na=False)]

        # Export panel
        st.markdown("---")
        st.markdown("#### :material/file_download: Export")
        st.caption(f"Showing **{len(view_df[view_df['Include']])}** included item(s) of **{len(edited_df)}** total.")

        included_view = view_df[view_df["Include"]]

        txt_export = format_checklist_txt(included_view)
        csv_export = format_checklist_csv(included_view)
        md_export = format_checklist_md(included_view)
        ics_export = format_checklist_ics(included_view, reference_date=meeting_date)

        exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)
        exp_col1.download_button(
            ":material/download: .txt",
            data=txt_export,
            file_name="action_items.txt",
            mime="text/plain",
            width='stretch',
        )
        exp_col2.download_button(
            ":material/download: .csv",
            data=csv_export,
            file_name="action_items.csv",
            mime="text/csv",
            width='stretch',
        )
        exp_col3.download_button(
            ":material/download: .md",
            data=md_export,
            file_name="action_items.md",
            mime="text/markdown",
            width='stretch',
        )
        exp_col4.download_button(
            ":material/calendar_month: .ics",
            data=ics_export.encode("utf-8"),
            file_name="action_items.ics",
            mime="text/calendar",
            width='stretch',
            help="Import into Google Calendar / Outlook / Apple Calendar.",
        )

    # ---------- Tab 2: Insights (charts) ----------
    with tab_insights:
        st.caption("Auto-generated dashboard from the extracted action items. Built with Altair — no extra dependencies beyond Streamlit.")

        if insights["total"] == 0:
            st.info("No data yet — extract some action items to see charts here.")
        else:
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("##### Priority distribution")
                pri_df = pd.DataFrame([
                    {"Band": b, "Count": c}
                    for b, c in insights["priority_counts"].items()
                ])
                pri_chart = alt.Chart(pri_df).mark_bar(cornerRadius=6).encode(
                    x=alt.X("Band:N", sort=["High", "Medium", "Low"], title="Priority"),
                    y=alt.Y("Count:Q", title=None),
                    color=alt.Color(
                        "Band:N",
                        scale=alt.Scale(
                            domain=["High", "Medium", "Low"],
                            range=["#F87171", "#FBBF24", "#34D399"],
                        ),
                        legend=None,
                    ),
                    tooltip=["Band", "Count"],
                ).properties(height=240)
                st.altair_chart(pri_chart, width='stretch')

                st.markdown("##### Deadline horizon")
                dl_df = pd.DataFrame([
                    {"Bucket": k, "Count": v}
                    for k, v in insights["deadline_horizon"].items()
                ])
                dl_chart = alt.Chart(dl_df).mark_bar(cornerRadius=6).encode(
                    x=alt.X("Count:Q", title=None),
                    y=alt.Y(
                        "Bucket:N",
                        sort=["overdue", "0-3 days", "4-7 days", "8-30 days", ">30 days", "no deadline"],
                        title=None,
                    ),
                    color=alt.condition(
                        alt.datum.Bucket == "overdue",
                        alt.value("#F87171"),
                        alt.value("#22D3EE"),
                    ),
                    tooltip=["Bucket", "Count"],
                ).properties(height=240)
                st.altair_chart(dl_chart, width='stretch')

            with chart_col2:
                st.markdown("##### Confidence distribution")
                conf_df = pd.DataFrame([
                    {"Band": b, "Count": c}
                    for b, c in insights["confidence_counts"].items()
                ])
                conf_chart = alt.Chart(conf_df).mark_bar(cornerRadius=6).encode(
                    x=alt.X("Band:N", sort=["High", "Medium", "Low"], title="Confidence"),
                    y=alt.Y("Count:Q", title=None),
                    color=alt.value("#818CF8"),
                    tooltip=["Band", "Count"],
                ).properties(height=240)
                st.altair_chart(conf_chart, width='stretch')

                st.markdown("##### Sentiment distribution")
                sent_df = pd.DataFrame([
                    {"Sentiment": s, "Count": c}
                    for s, c in insights["sentiment_counts"].items()
                ])
                sent_chart = alt.Chart(sent_df).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta("Count:Q", title=None),
                    color=alt.Color(
                        "Sentiment:N",
                        scale=alt.Scale(
                            domain=["Positive", "Neutral", "Negative"],
                            range=["#34D399", "#94A3B8", "#F87171"],
                        ),
                    ),
                    tooltip=["Sentiment", "Count"],
                ).properties(height=240)
                st.altair_chart(sent_chart, width='stretch')

            st.markdown("---")
            st.markdown("##### Owner workload")
            if not insights["owner_workload"]:
                st.info("No owners detected in the extracted items — try a sample with named people.")
            else:
                ow_df = pd.DataFrame(insights["owner_workload"], columns=["Owner", "Tasks"])
                ow_chart = alt.Chart(ow_df).mark_bar(cornerRadius=6).encode(
                    x=alt.X("Tasks:Q", title="Number of tasks"),
                    y=alt.Y("Owner:N", sort="-x", title=None),
                    color=alt.value("#22D3EE"),
                    tooltip=["Owner", "Tasks"],
                ).properties(height=300)
                st.altair_chart(ow_chart, width='stretch')

    # ---------- Tab 3: Summary ----------
    with tab_summary:
        st.markdown("##### Extractive Meeting Summary")
        st.caption(
            "Auto-generated by ranking every sentence by **cue density** (how many action-item "
            "cues fired per word, with a small length bonus). This is a TextRank-style signal "
            "computed without any ML — it reuses the same cue vocabulary that drives flagging, "
            "so the summary naturally surfaces the most action-dense sentences."
        )
        if st.session_state.summary_text:
            st.markdown(
                f"""<div class="callout success">{st.session_state.summary_text}</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.info("No summary available — extract some notes first.")

        st.markdown("---")
        st.markdown("##### Quick stats")
        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("Total sentences processed", stats["total"])
        s_col2.metric("Participants detected", len(st.session_state.participants))
        s_col3.metric("Key topics detected", len(st.session_state.key_topics))

    # ---------- Tab 4: Participants ----------
    with tab_people:
        st.markdown("##### Participants")
        st.caption(
            "Every PERSON entity mentioned anywhere in the notes — not just inside flagged "
            "action items. Detected via spaCy's named-entity recognition (NER) layer. The "
            "order is the order of first appearance."
        )
        if st.session_state.participants:
            for i, name in enumerate(st.session_state.participants, start=1):
                st.markdown(
                    f"<span class='status-pill info'>{i}. {name}</span>&nbsp;",
                    unsafe_allow_html=True,
                )
            st.markdown("")  # newline
        else:
            st.info("No participants detected — try loading a sample with named people.")

    # ---------- Tab 5: Topics ----------
    with tab_topics:
        st.markdown("##### Key topics / keywords")
        st.caption(
            "Top noun_chunks mined from the notes — a quick view of what the meeting was *about*. "
            "Uses spaCy's noun_chunks iterator + a small stopword filter."
        )
        if st.session_state.key_topics:
            topics_df = pd.DataFrame(st.session_state.key_topics, columns=["Topic", "Mentions"])
            topics_df["Topic"] = topics_df["Topic"].str.title()
            st.dataframe(topics_df, hide_index=True, width='stretch')

            # As a chip cloud
            st.markdown("")
            st.markdown("##### Topic chips")
            chips = " ".join(
                f"<span class='status-pill info'>{name} ({count})</span>&nbsp;"
                for name, count in st.session_state.key_topics
            )
            st.markdown(chips, unsafe_allow_html=True)
        else:
            st.info("No topics detected — extract some notes first.")

    # ---------- Tab 6: Why was this flagged? ----------
    with tab_why:
        st.markdown("##### Why was this flagged?")
        st.caption(
            "Per-row explainability: the original sentence, every cue that fired, the detected "
            "owner and deadline, and the priority + sentiment signals. This is the audit trail."
        )
        lookup = st.session_state.get("item_lookup", {})
        for _, row in edited_df.iterrows():
            item = lookup.get(row["id"])
            if item is None:
                continue
            title = row['Task'][:80] + ("…" if len(row['Task']) > 80 else "")
            with st.expander(f"#{row['id']} · {title}"):
                e_col1, e_col2, e_col3 = st.columns([1, 1, 1])
                with e_col1:
                    st.markdown("**Original sentence**")
                    st.write(item.sentence)
                with e_col2:
                    st.markdown("**Matched cues**")
                    if item.matched_cues:
                        st.markdown("".join(f"<span class='status-pill info'>{c}</span>&nbsp;" for c in item.matched_cues), unsafe_allow_html=True)
                    else:
                        st.write("none")
                    st.markdown("")
                    st.markdown("**Owner detected**")
                    st.write(item.owner or "None")
                with e_col3:
                    st.markdown("**Deadline detected**")
                    if item.deadline:
                        st.write(f"{item.deadline} (from \"{item.deadline_raw}\")")
                    elif item.deadline_raw:
                        st.write(f"Could not resolve exact date from \"{item.deadline_raw}\"")
                    else:
                        st.write("None")
                    st.markdown("**Priority & Sentiment**")
                    pri_pill = (
                        "<span class='status-pill danger'>High</span>"
                        if item.priority_band == "High"
                        else f"<span class='status-pill warn'>{item.priority_band}</span>"
                        if item.priority_band == "Medium"
                        else f"<span class='status-pill success'>{item.priority_band}</span>"
                    )
                    sent_pill = (
                        "<span class='status-pill success'>Positive</span>"
                        if item.sentiment == "Positive"
                        else f"<span class='status-pill danger'>Negative</span>"
                        if item.sentiment == "Negative"
                        else f"<span class='status-pill info'>Neutral</span>"
                    )
                    st.markdown(
                        f"{pri_pill} score={item.priority_score} &nbsp; {sent_pill}",
                        unsafe_allow_html=True,
                    )

