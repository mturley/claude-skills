#!/usr/bin/env python3
"""Shared formatting utilities for Claude Code skills.

Provides markdown formatting, date formatting, and link generation.
Used by /reviews-status and /sprint-status skills.

Uses only Python stdlib. No pip dependencies.
"""

import json
import sys
from datetime import datetime


JIRA_BASE = "https://issues.redhat.com/browse"

TYPE_EMOJI = {
    "Bug": "\U0001f7e5",        # 🟥
    "Story": "\U0001f7e9",      # 🟩
    "Task": "\u2611\ufe0f",     # ☑️
    "Sub-task": "\U0001f539",   # 🔹
    "Epic": "\u26a1",           # ⚡
    "Initiative": "\U0001f7e7", # 🟧
    "Outcome": "\U0001f7e6",    # 🟦
    "Spike": "\U0001f52c",      # 🔬
}

PRIORITY_EMOJI = {
    "Blocker": "\u26d4",        # ⛔
    "Critical": "\U0001f53a",   # 🔺
    "Major": "\U0001f536",      # 🔶
    "Minor": "\U0001f53d",      # 🔽
    "Normal": "\U0001f535",     # 🔵
    "Undefined": "\u26aa",      # ⚪
}


def format_type(issue_type):
    """Format issue type with emoji prefix."""
    emoji = TYPE_EMOJI.get(issue_type, "")
    if emoji:
        return f"{emoji} {issue_type}"
    return issue_type or "--"


def format_priority(priority):
    """Format priority with emoji prefix."""
    emoji = PRIORITY_EMOJI.get(priority, "")
    if emoji:
        return f"{emoji} {priority}"
    return priority or "--"


def truncate_title(title, max_len=50):
    """Truncate title to max_len characters with ellipsis."""
    if len(title) <= max_len:
        return title
    return title[:max_len - 3] + "..."


def format_date(iso_str, today):
    """Format ISO date string as relative date.

    - "today" for today
    - "Mon DD" for current year
    - "Mon YYYY" for older
    """
    if not iso_str:
        return "--"
    try:
        # Normalize timezone formats: "Z" -> "+00:00", "+0000" -> "+00:00"
        s = iso_str.replace("Z", "+00:00")
        # Handle "+0000" or "-0500" (no colon) -> "+00:00" or "-05:00"
        import re
        s = re.sub(r'([+-])(\d{2})(\d{2})$', r'\1\2:\3', s)
        dt = datetime.fromisoformat(s)
        d = dt.date()
        if d == today:
            return "today"
        if d.year == today.year:
            return dt.strftime("%b %d")
        return dt.strftime("%b %Y")
    except (ValueError, TypeError):
        return "--"


def format_pr_link(pr):
    """Format PR as [repo#number](url)."""
    repo = pr.get("repo", "")
    number = pr.get("number", 0)
    url = pr.get("url", "")
    return f"[{repo}#{number}]({url})"


def format_jira_link(jira):
    """Format Jira issue as [KEY](url) (emoji Type)."""
    key = jira.get("key", "")
    issue_type = jira.get("type", "")
    return f"[{key}]({JIRA_BASE}/{key}) ({format_type(issue_type)})"


def format_epic(epic_key, epics):
    """Format epic as [KEY](url) (Short Name)."""
    if not epic_key:
        return "--"
    short_name = epics.get(epic_key, "")
    if short_name:
        return f"[{epic_key}]({JIRA_BASE}/{epic_key}) ({short_name})"
    return f"[{epic_key}]({JIRA_BASE}/{epic_key})"


def reverse_date(iso_str):
    """Return a value that sorts dates in descending order."""
    if not iso_str:
        return ""
    # Invert the string for reverse sort
    return "".join(chr(255 - ord(c)) if ord(c) < 256 else c for c in iso_str)


def read_stdin():
    """Read and parse JSON from stdin with clear error messages."""
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin. Pipe JSON data to this script.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    from datetime import date

    today = date(2026, 3, 5)

    assert truncate_title("Short title") == "Short title"
    assert truncate_title("A" * 55) == "A" * 47 + "..."
    assert truncate_title("Exactly fifty characters long for testing!") == "Exactly fifty characters long for testing!"
    assert len("Exactly fifty characters long for testing!") <= 50

    assert format_date("2026-03-05T12:00:00Z", today) == "today"
    assert format_date("2026-03-01T12:00:00Z", today) == "Mar 01"
    assert format_date("2025-06-15T12:00:00Z", today) == "Jun 2025"
    assert format_date("", today) == "--"
    assert format_date(None, today) == "--"

    pr = {"repo": "odh-dashboard", "number": 6466, "url": "https://github.com/opendatahub-io/odh-dashboard/pull/6466"}
    assert format_pr_link(pr) == "[odh-dashboard#6466](https://github.com/opendatahub-io/odh-dashboard/pull/6466)"

    jira = {"key": "RHOAIENG-51543", "type": "Bug"}
    link = format_jira_link(jira)
    assert "RHOAIENG-51543" in link
    assert "(\U0001f7e5 Bug)" in link

    # format_type tests
    assert format_type("Bug") == "\U0001f7e5 Bug"
    assert format_type("Story") == "\U0001f7e9 Story"
    assert format_type("Task") == "\u2611\ufe0f Task"
    assert format_type("Sub-task") == "\U0001f539 Sub-task"
    assert format_type("UnknownType") == "UnknownType"
    assert format_type("") == "--"

    # format_priority tests
    assert format_priority("Blocker") == "\u26d4 Blocker"
    assert format_priority("Critical") == "\U0001f53a Critical"
    assert format_priority("Major") == "\U0001f536 Major"
    assert format_priority("Minor") == "\U0001f53d Minor"
    assert format_priority("Normal") == "\U0001f535 Normal"
    assert format_priority("Undefined") == "\u26aa Undefined"
    assert format_priority("SomethingElse") == "SomethingElse"
    assert format_priority("") == "--"

    epics = {"RHOAIENG-27992": "OCI Storage"}
    assert "OCI Storage" in format_epic("RHOAIENG-27992", epics)
    assert format_epic(None, epics) == "--"
    assert "RHOAIENG-99999" in format_epic("RHOAIENG-99999", epics)

    # reverse_date should sort descending
    assert reverse_date("2026-03-05") > reverse_date("2026-03-06")
    assert reverse_date("") == ""

    print("All format_utils tests passed.")
