"""
utils.py
"""

from __future__ import annotations

import io
from datetime import date, datetime, timedelta
from typing import Iterable, Optional as OptionalDate

import pandas as pd

from extractor import ActionItem


# ---------------------------------------------------------------------------
# ActionItem -> DataFrame
# ---------------------------------------------------------------------------

def items_to_dataframe(items: Iterable[ActionItem]) -> pd.DataFrame:
    """Convert a list of ActionItem objects into the dataframe shown in
    the Streamlit data_editor table."""
    rows = []
    for item in items:
        rows.append(
            {
                "Include": True,
                "Task": item.task,
                "Owner": item.owner or "",
                "Deadline": item.deadline or "",
                "Deadline (raw)": item.deadline_raw or "",
                "Confidence": item.confidence,
                "Priority": item.priority_band,
                "Priority Score": item.priority_score,
                "Sentiment": item.sentiment,
                "id": item.id,
            }
        )
    columns = [
        "Include", "Task", "Owner", "Deadline", "Deadline (raw)",
        "Confidence", "Priority", "Priority Score", "Sentiment", "id",
    ]
    return pd.DataFrame(rows, columns=columns)


# ---------------------------------------------------------------------------
# Plain-text checklist
# ---------------------------------------------------------------------------

def format_checklist_txt(df: pd.DataFrame) -> str:
    """Render the (filtered) results dataframe as a plain-text checklist,
    suitable for pasting into an email or Slack message."""
    lines = ["Action Items", "=" * 40, ""]

    if df.empty:
        lines.append("(No action items)")
        return "\n".join(lines)

    for _, row in df.iterrows():
        checkbox = "[ ]"
        line = f"{checkbox} {row['Task']}"
        details = []
        if row.get("Owner"):
            details.append(f"Owner: {row['Owner']}")
        if row.get("Deadline"):
            details.append(f"Due: {row['Deadline']}")
        elif row.get("Deadline (raw)"):
            details.append(f"Due: {row['Deadline (raw)']} (unresolved)")
        details.append(f"Confidence: {row['Confidence']}")
        if "Priority" in row:
            details.append(f"Priority: {row['Priority']}")
        if details:
            line += "\n      " + " | ".join(details)
        lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def format_checklist_csv(df: pd.DataFrame) -> str:
    """Render the (filtered) results dataframe as CSV text."""
    export_df = df.drop(columns=["Include", "id"], errors="ignore")
    buffer = io.StringIO()
    export_df.to_csv(buffer, index=False)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Markdown checklist (NEW)
# ---------------------------------------------------------------------------

def format_checklist_md(df: pd.DataFrame) -> str:
    """Render the dataframe as a Markdown checklist (great for Notion / README)."""
    lines = ["## Action Items", ""]
    if df.empty:
        lines.append("_(No action items)_")
        return "\n".join(lines)

    for _, row in df.iterrows():
        line = f"- [ ] **{row['Task']}**"
        extras = []
        if row.get("Owner"):
            extras.append(f"@{row['Owner']}")
        if row.get("Deadline"):
            extras.append(f"due `{row['Deadline']}`")
        elif row.get("Deadline (raw)"):
            extras.append(f"due _{row['Deadline (raw)']}_ (unresolved)")
        if "Priority" in row:
            extras.append(f"priority `{row['Priority']}`")
        if extras:
            line += " — " + " · ".join(extras)
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# iCalendar (.ics) export (NEW)
# ---------------------------------------------------------------------------

def format_checklist_ics(
    df: pd.DataFrame,
    calendar_name: str = "NoteCraft Action Items",
    reference_date: OptionalDate = None,
) -> str:
    """Render included action items as an iCalendar (.ics) string.

    Each row becomes a VEVENT:
      - SUMMARY   = task text
      - DTSTART   = deadline (all-day event) — falls back to "today" if missing
      - DTEND     = same day
      - DESCRIPTION = original sentence + matched cues + confidence
      - ATTENDEE  = owner (if present)
      - CATEGORIES = priority band + sentiment
    """
    if reference_date is None:
        reference_date = date.today()

    def _fmt_dt(d: date) -> str:
        return d.strftime("%Y%m%d")

    def _escape(text: str) -> str:
        # RFC 5545 escaping
        if not text:
            return ""
        return (
            text.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
        )

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NoteCraft//Meeting Notes Action Items//EN",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
        "CALSCALE:GREGORIAN",
    ]

    if df.empty:
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for idx, row in df.iterrows():
        deadline_str = row.get("Deadline") if "Deadline" in row else None
        try:
            due_date = date.fromisoformat(deadline_str) if deadline_str else reference_date
        except (ValueError, TypeError):
            due_date = reference_date

        owner = row.get("Owner") if "Owner" in row else ""
        priority = row.get("Priority") if "Priority" in row else ""
        confidence = row.get("Confidence") if "Confidence" in row else ""
        sentiment = row.get("Sentiment") if "Sentiment" in row else ""
        task = row.get("Task", "")
        raw_deadline = row.get("Deadline (raw)") if "Deadline (raw)" in row else ""

        description_parts = []
        if raw_deadline:
            description_parts.append(f"Raw deadline: {raw_deadline}")
        if confidence:
            description_parts.append(f"Confidence: {confidence}")
        if sentiment:
            description_parts.append(f"Sentiment: {sentiment}")
        description = " | ".join(description_parts) if description_parts else "NoteCraft action item"

        uid = f"notecraft-{idx}-{now_stamp}@notecraft.local"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;VALUE=DATE:{_fmt_dt(due_date)}",
            f"DTEND;VALUE=DATE:{_fmt_dt(due_date + timedelta(days=1))}",
            f"SUMMARY:{_escape(task)}",
            f"DESCRIPTION:{_escape(description)}",
        ])
        if owner:
            lines.append(f"ATTENDEE;CN={_escape(owner)}:mailto:no-reply@notecraft.local")
        if priority:
            lines.append(f"CATEGORIES:{_escape(priority)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


# ---------------------------------------------------------------------------
# Summary stats
# ---------------------------------------------------------------------------

def summary_stats(df: pd.DataFrame) -> dict:
    """Compute the summary metrics shown at the top of the results area."""
    total = len(df)
    with_owner = int((df["Owner"] != "").sum()) if total else 0
    with_deadline = int((df["Deadline"] != "").sum()) if total else 0
    return {
        "total": total,
        "with_owner": with_owner,
        "with_deadline": with_deadline,
    }


# ---------------------------------------------------------------------------
# Dashboard insights (NEW)
# ---------------------------------------------------------------------------

def build_insights(df: pd.DataFrame, reference_date: OptionalDate = None) -> dict:
    """Return a dict of dashboard-ready aggregates used by the Insights tab."""
    if reference_date is None:
        reference_date = date.today()

    total = len(df)
    if total == 0:
        return {
            "total": 0,
            "priority_counts": {"High": 0, "Medium": 0, "Low": 0},
            "sentiment_counts": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "confidence_counts": {"High": 0, "Medium": 0, "Low": 0},
            "owner_workload": [],
            "deadline_horizon": {"overdue": 0, "0-3 days": 0, "4-7 days": 0, "8-30 days": 0, ">30 days": 0, "no deadline": 0},
            "completion_pct": 0.0,
        }

    # Priority distribution
    priority_counts = {"High": 0, "Medium": 0, "Low": 0}
    if "Priority" in df.columns:
        for band in df["Priority"]:
            if band in priority_counts:
                priority_counts[band] += 1

    # Sentiment distribution
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    if "Sentiment" in df.columns:
        for s in df["Sentiment"]:
            if s in sentiment_counts:
                sentiment_counts[s] += 1

    # Confidence distribution
    confidence_counts = {"High": 0, "Medium": 0, "Low": 0}
    if "Confidence" in df.columns:
        for c in df["Confidence"]:
            if c in confidence_counts:
                confidence_counts[c] += 1

    # Owner workload (top 8)
    owner_workload_pairs = []
    if "Owner" in df.columns:
        owners = [o for o in df["Owner"] if o]
        if owners:
            from collections import Counter
            for owner_name, count in Counter(owners).most_common(8):
                owner_workload_pairs.append((owner_name, count))

    # Deadline horizon
    deadline_horizon = {
        "overdue": 0, "0-3 days": 0, "4-7 days": 0,
        "8-30 days": 0, ">30 days": 0, "no deadline": 0,
    }
    if "Deadline" in df.columns:
        for d in df["Deadline"]:
            if not d:
                deadline_horizon["no deadline"] += 1
                continue
            try:
                due = date.fromisoformat(d)
                delta = (due - reference_date).days
                if delta < 0:
                    deadline_horizon["overdue"] += 1
                elif delta <= 3:
                    deadline_horizon["0-3 days"] += 1
                elif delta <= 7:
                    deadline_horizon["4-7 days"] += 1
                elif delta <= 30:
                    deadline_horizon["8-30 days"] += 1
                else:
                    deadline_horizon[">30 days"] += 1
            except (ValueError, TypeError):
                deadline_horizon["no deadline"] += 1

    # Completion % = rows still included (Include=True) / total
    completion_pct = 0.0
    if "Include" in df.columns:
        included = int(df["Include"].sum())
        completion_pct = round(included / total * 100, 1) if total else 0.0

    return {
        "total": total,
        "priority_counts": priority_counts,
        "sentiment_counts": sentiment_counts,
        "confidence_counts": confidence_counts,
        "owner_workload": owner_workload_pairs,
        "deadline_horizon": deadline_horizon,
        "completion_pct": completion_pct,
    }


# ---------------------------------------------------------------------------
# Sample notes
# ---------------------------------------------------------------------------

SAMPLE_NOTES = {
    "Project sync (informal bullets)": """\
Team sync notes - 18 July

- Discussed the Q3 roadmap and everyone seemed aligned on priorities.
- Priya will send the updated budget spreadsheet by Friday.
- We need to review the vendor contracts before next week.
- John to follow up with the design team about the new mockups.
- Should we look into the new analytics tool at some point? Maybe.
- Sam's task is to schedule the client demo for next Tuesday.
- The meeting overall went well and morale seems high.
- Please finalize the slide deck by EOD tomorrow.
- Assigned to Maria: update the onboarding docs.
- Reminder: the office is closed next Monday for the holiday.
""",
    "Client call (paragraph style)": """\
Notes from the client call this afternoon. The client is happy with progress
so far and wants to move to the next phase soon. Alex will draft the revised
proposal and send it to the client by next Wednesday. We also need to
confirm the new pricing with finance before we can share anything.
There was a general discussion about long-term strategy but no firm
decisions were made. Nina must submit the signed contract by end of week.
Someone should double check the timeline slide, it looked outdated.
Follow up with legal about the NDA next week.
""",
    "Sprint retrospective (mixed)": """\
Sprint 14 retro - 22 July

- The payment gateway integration is blocked and needs immediate attention.
- Alex will investigate the API timeout issue by tomorrow.
- We need to update the deployment docs before next Friday.
- The new feature flag system is working great, the team is happy.
- Priya should schedule a security review with the infra team next week.
- Action item: Marcus to fix the broken CI pipeline by EOD.
- Assigned to Lena: prepare the customer feedback summary for next Tuesday.
- Concerns were raised about the database migration timeline.
- Someone must follow up with the vendor about the licensing issue.
- The team agreed the code quality has improved significantly this sprint.
- Reminder: quarterly review meeting is scheduled for next month.
""",
}
