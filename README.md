# NoteCraft — Meeting Notes → Action Items Extractor

A lightweight, free, fully offline tool that turns rough meeting notes into
a clean checklist of action items — each with a detected **owner**,
**deadline**, **confidence score**, **priority**, and **sentiment** — using
classical rule-based NLP (no LLMs, no paid APIs, no model training).

## What's New in v2.0

* **Bug fix**: The "Include" checkbox in the results table no longer
  resets the page when toggled. Root cause was a session_state feedback
  loop in the data_editor; fixed by keeping `results_df` as the original
  extracted dataframe and using the widget's `key=` parameter to track
  edits.
* **Six new NLP features**: Priority Score, Sentiment per item,
  extractive Meeting Summary, Participants List (NER), Key Topics
  (noun_chunks), and a Stats Dashboard (Altair charts).
* **New exports**: `.md` (Markdown checklist) and `.ics` (iCalendar —
  imports into Google Calendar / Outlook / Apple Calendar).
* **Dark Premium UI redesign**: deep slate background, neon-cyan accents,
  hero header, six-tab layout (Checklist / Insights / Summary /
  Participants / Topics / Why flagged).
* **Third sample notes** added (Sprint retrospective, mixed style) for
  richer demos.

## Features

- Paste notes or upload a `.txt` file
- Three built-in sample note sets (bullet-style, paragraph-style, mixed)
- Detects action items using modal verbs, imperative mood, task-signaling
  verbs, and assignment phrasing
- Extracts **owner** (via NER + dependency parsing) and **deadline** (via
  NER `DATE` entities + regex fallback for phrases like "next week")
- **Priority** (1–5, new) — combines confidence + deadline urgency + owner
- **Sentiment** per item (Positive / Neutral / Negative, new)
- **Extractive meeting summary** (top-3 sentences by cue density, new)
- **Participants list** — every PERSON mentioned (new)
- **Key topics** — top noun_chunks (new)
- **Stats dashboard** — 5 Altair charts (new)
- Editable results table with filters (priority, confidence, sentiment, search)
- "Why was this flagged?" panel per row for explainability
- Export as `.txt`, `.csv`, `.md`, or `.ics`
- Runs 100% locally — nothing leaves your machine

## Project structure

```
NoteCraft-main/
├── app.py                 # Streamlit UI (Dark Premium theme, 6 tabs)
├── extractor.py           # Core NLP logic (flagging, NER, dates, priority, sentiment, summary, participants, topics)
├── utils.py               # Formatting, export (.txt/.csv/.md/.ics), insights, sample notes
├── samples/               # Example meeting notes for testing
│   ├── sample_notes_1.txt
│   └── sample_notes_2.txt
├── tests/
│   └── test_extractor.py  # 27 tests (all passing)
├── requirements.txt
├── setup.sh               # downloads the spaCy model
└── README.md
```

## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download the spaCy English model
bash setup.sh
# (or directly: python -m spacy download en_core_web_sm)
```

## Run

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

## Test

```bash
pytest
```

All 27 tests pass.

## How detection works

For every sentence, the tool checks for these cue categories (see
`extractor.py::classify_sentence`):

| Cue | Example |
|---|---|
| Modal/obligation verb | "will", "need to", "should", "must" |
| Imperative mood | "Send the report by Friday." |
| Task-signaling verb | "review", "schedule", "follow up", "finalize" |
| Assignment phrasing | "Priya will...", "assigned to Sam", "Sam's task is..." |

A sentence needs **1+** matched cue to be flagged. Confidence is Low (1
cue), Medium (2 cues), or High (3+ cues, or an owner *and* deadline both
found). Priority (new) is a 1–5 integer that adds deadline urgency and
owner presence to the confidence score.

## Known limitations

- Implicit or hedged action items ("maybe we should look into X") may be
  missed or under-confident.
- Pronoun coreference ("she'll handle it") is intentionally out of scope.
- Informal date phrases like "ASAP" or "sometime next month" may not
  resolve to an exact date (the raw phrase is still shown).
- Occasional false positives are expected; use the "Include" checkbox to
  remove them before exporting.
- The sentiment scorer doesn't understand negation ("not happy" → Positive
  is a known false positive; planned for v3).

## Requirements

- Python 3.10+
- streamlit (>=1.30)
- spacy (`en_core_web_sm`)
- pandas
- python-dateutil
- altair (new in v2)
- pytest (for running tests)

