#!/usr/bin/env python3
"""Render a Jira activity timeline from changelog and comment data.

Reads JSON from stdin with raw Jira getIssue results (with changelogs)
and getIssueComments results. Filters for the specified user's actions,
converts timestamps to the target timezone, and renders a markdown
timeline with merged consecutive rows, issue type/priority emojis,
and hyperlinked Jira issues and PRs.

Uses only Python stdlib. No pip dependencies.
"""

import json
import os
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from format_utils import TYPE_EMOJI, PRIORITY_EMOJI, JIRA_BASE

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


# Fields to skip entirely (noisy/internal)
SKIP_FIELDS = {"Rank", "Workflow", "RemoteIssueLink"}

# Max length for field values in the action column
MAX_VALUE_LEN = 200


def parse_iso_datetime(s):
    """Parse Jira ISO datetime string to aware datetime."""
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    s = re.sub(r'([+-])(\d{2})(\d{2})$', r'\1\2:\3', s)
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def convert_tz(dt, tz_name):
    """Convert datetime to target timezone."""
    if not dt:
        return dt
    if ZoneInfo:
        try:
            return dt.astimezone(ZoneInfo(tz_name))
        except Exception:
            pass
    # Fallback: assume UTC-5 for America/New_York (no DST handling)
    if "New_York" in tz_name or "Eastern" in tz_name:
        from datetime import timedelta
        return dt.astimezone(timezone(timedelta(hours=-5)))
    return dt


def detect_single_issue(data):
    """Parse a single getIssue result (possibly MCP-wrapped)."""
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        inner = json.loads(data[0]["text"])
        return detect_single_issue(inner)
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict) and "key" in data["data"]:
            return data["data"]
        if "key" in data and "fields" in data:
            return data
    return None


def detect_comments(data):
    """Parse a getIssueComments result (possibly MCP-wrapped)."""
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        inner = json.loads(data[0]["text"])
        return detect_comments(inner)
    if isinstance(data, dict):
        if "data" in data and "comments" in data["data"]:
            return data["data"]["comments"]
        if "comments" in data:
            return data["comments"]
    return []


def format_type(issue_type):
    """Format issue type with emoji."""
    emoji = TYPE_EMOJI.get(issue_type, "")
    return f"{emoji} {issue_type}" if emoji else (issue_type or "--")


def format_priority(priority):
    """Format priority with emoji."""
    emoji = PRIORITY_EMOJI.get(priority, "")
    return f"{emoji} {priority}" if emoji else (priority or "--")


def truncate(s, max_len=MAX_VALUE_LEN):
    """Truncate a string with ellipsis if too long."""
    if not s or len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


def format_action(field, from_str, to_str):
    """Format a changelog item as a readable action string."""
    # Description changes are summarized to avoid verbose diffs
    if field.lower() == "description":
        return "Updated description"

    from_str = truncate(from_str or "")
    to_str = truncate(to_str or "")

    if from_str and to_str:
        return f"**{field}**: {from_str} → {to_str}"
    elif to_str:
        return f"**{field}**: set to {to_str}"
    elif from_str:
        return f"**{field}**: removed {from_str}"
    else:
        return f"**{field}**: changed"


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)

    username_keys = set(data.get("username_keys", []))
    tz_name = data.get("timezone", "America/New_York")
    cutoff_str = data.get("cutoff", "")
    today_str = data.get("today", "")
    issues_raw = data.get("issues", {})
    comments_raw = data.get("comments", {})

    cutoff = None
    if cutoff_str:
        cutoff = datetime.fromisoformat(cutoff_str + "T00:00:00+00:00")

    timeline = []
    issue_meta = {}  # Cache issue metadata

    # Process each issue's changelog
    for issue_key, raw_issue in issues_raw.items():
        issue = detect_single_issue(raw_issue)
        if not issue:
            continue

        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        issue_type_obj = fields.get("issuetype", {}) or {}
        issue_type = issue_type_obj.get("name", "")
        priority_obj = fields.get("priority", {}) or {}
        priority = priority_obj.get("name", "")

        issue_meta[issue_key] = {
            "summary": summary,
            "type": issue_type,
            "priority": priority,
        }

        changelog = issue.get("changelog", {})
        if not changelog:
            continue

        for history in changelog.get("histories", []):
            author = history.get("author", {})
            author_name = author.get("name", "")
            author_key = author.get("key", "")

            if author_name not in username_keys and author_key not in username_keys:
                continue

            created = history.get("created", "")
            dt = parse_iso_datetime(created)
            if not dt or (cutoff and dt < cutoff):
                continue

            for item in history.get("items", []):
                field = item.get("field", "")
                if field in SKIP_FIELDS:
                    continue

                action = format_action(
                    field,
                    item.get("fromString", ""),
                    item.get("toString", ""),
                )

                dt_local = convert_tz(dt, tz_name)

                timeline.append({
                    "dt": dt_local,
                    "key": issue_key,
                    "summary": summary,
                    "type": issue_type,
                    "priority": priority,
                    "action": action,
                })

    # Process comments
    for issue_key, raw_comments in comments_raw.items():
        comments = detect_comments(raw_comments)

        meta = issue_meta.get(issue_key, {})
        summary = meta.get("summary", "")
        issue_type = meta.get("type", "")
        priority = meta.get("priority", "")

        for comment in comments:
            author = comment.get("author", {})
            author_name = author.get("name", "")
            author_key = author.get("key", "")

            if author_name not in username_keys and author_key not in username_keys:
                continue

            created = comment.get("created", "")
            dt = parse_iso_datetime(created)
            if not dt or (cutoff and dt < cutoff):
                continue

            body = comment.get("body", "")
            body_lines = body.strip().split("\n")
            preview = body_lines[0][:200] if body_lines else ""
            if len(body_lines) > 1 or (body_lines and len(body_lines[0]) > 200):
                preview += "..."

            dt_local = convert_tz(dt, tz_name)

            timeline.append({
                "dt": dt_local,
                "key": issue_key,
                "summary": summary,
                "type": issue_type,
                "priority": priority,
                "action": f"**Comment:** \"{preview}\"",
            })

    # Sort chronologically
    timeline.sort(key=lambda x: x["dt"])

    if not timeline:
        print("No activity found for the specified user and time period.")
        return

    # Group by day
    days = OrderedDict()
    for entry in timeline:
        day_key = entry["dt"].strftime("%Y-%m-%d")
        day_name = entry["dt"].strftime("%A, %B %-d")
        if day_key not in days:
            days[day_key] = {"label": day_name, "entries": []}
        days[day_key]["entries"].append(entry)

    # Render
    lines = ["## Jira Activity Timeline", ""]
    lines.append("All times are Eastern Time (ET).")
    lines.append("")

    for day_key, day in days.items():
        heading = f"### {day['label']}"
        if day_key == today_str:
            heading += " (today)"
        lines.append(heading)
        lines.append("")
        lines.append("| Time (ET) | Issue | Type | Priority | Action |")
        lines.append("|-----------|-------|------|----------|--------|")

        prev_key = None
        for entry in day["entries"]:
            time_str = entry["dt"].strftime("%-I:%M %p")

            if entry["key"] == prev_key:
                # Merge cells — leave issue/type/priority blank
                lines.append(f"| {time_str} | | | | {entry['action']} |")
            else:
                type_str = format_type(entry["type"])
                pri_str = format_priority(entry["priority"])
                issue_link = (
                    f"[{entry['key']}]({JIRA_BASE}/{entry['key']})"
                    f" — {entry['summary']}"
                )
                lines.append(
                    f"| {time_str} | {issue_link} | {type_str}"
                    f" | {pri_str} | {entry['action']} |"
                )
                prev_key = entry["key"]

        lines.append("")

    # Summary
    lines.append("---")
    lines.append("")
    unique_issues = set(e["key"] for e in timeline)
    comment_count = sum(
        1 for e in timeline if e["action"].startswith("**Comment:**")
    )
    changelog_count = len(timeline) - comment_count
    lines.append(
        f"**Summary:** {changelog_count} changelog action(s)"
        f" + {comment_count} comment(s)"
        f" across {len(unique_issues)} issue(s)."
    )

    print("\n".join(lines))


if __name__ == "__main__":
    main()
