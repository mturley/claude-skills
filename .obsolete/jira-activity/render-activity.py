#!/usr/bin/env python3
"""Render a Jira activity timeline from search results and comment data.

Reads Jira searchIssues results (with expand=changelog) and
getIssueComments results from persisted files. Filters for the specified
user's actions, converts timestamps to the target timezone, and renders
a markdown timeline with merged consecutive rows, issue type/priority
emojis, and hyperlinked Jira issues and PRs.

Usage:
    python3 render-activity.py \
        --username-keys mikejturley mturley \
        --timezone America/New_York \
        --cutoff 2026-03-02 \
        --today 2026-03-09 \
        --search-files /path/to/assignee.json /path/to/watcher.json ... \
        --comment-files RHOAIENG-51543=/path/to/comments1.json ...

Uses only Python stdlib. No pip dependencies.
"""

import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from format_utils import TYPE_EMOJI, PRIORITY_EMOJI, JIRA_BASE
from jira_utils import detect_and_parse_jira

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


def load_issues_from_search_files(search_files):
    """Load and deduplicate issues from search result files.

    Each file is a Jira searchIssues result (with expand=changelog),
    possibly MCP-wrapped. Returns a dict of issue_key -> issue_data.
    """
    issues = {}
    for file_path in search_files:
        if not os.path.exists(file_path):
            print(f"Warning: search file not found: {file_path}", file=sys.stderr)
            continue
        with open(file_path) as f:
            data = json.load(f)
        issue_list = detect_and_parse_jira(data)
        for issue in issue_list:
            key = issue.get("key", "")
            if key and key not in issues:
                issues[key] = issue
    return issues


def load_comments_from_files(comment_specs):
    """Load comments from file paths.

    Each spec is "ISSUE_KEY=/path/to/file.json".
    Returns a dict of issue_key -> list of comment dicts.
    """
    comments = {}
    for spec in comment_specs:
        if "=" not in spec:
            print(f"Warning: invalid comment spec (expected KEY=/path): {spec}", file=sys.stderr)
            continue
        issue_key, file_path = spec.split("=", 1)
        if not os.path.exists(file_path):
            print(f"Warning: comment file not found: {file_path}", file=sys.stderr)
            continue
        with open(file_path) as f:
            data = json.load(f)
        comments[issue_key] = detect_comments(data)
    return comments


def main():
    parser = argparse.ArgumentParser(description="Render Jira activity timeline.")
    parser.add_argument("--username-keys", nargs="+", required=True,
                        help="Jira username and key variants for the user")
    parser.add_argument("--timezone", default="America/New_York",
                        help="IANA timezone name (default: America/New_York)")
    parser.add_argument("--cutoff", required=True,
                        help="Start date for activity window (YYYY-MM-DD)")
    parser.add_argument("--today", required=True,
                        help="Today's date (YYYY-MM-DD)")
    parser.add_argument("--search-files", nargs="+", required=True,
                        help="Paths to Jira search result files (with expand=changelog)")
    parser.add_argument("--comment-files", nargs="*", default=[],
                        help="Comment file specs as ISSUE_KEY=/path/to/file.json")
    args = parser.parse_args()

    username_keys = set(args.username_keys)
    tz_name = args.timezone
    cutoff_str = args.cutoff
    today_str = args.today

    cutoff = None
    if cutoff_str:
        cutoff = datetime.fromisoformat(cutoff_str + "T00:00:00+00:00")

    # Load issues from search result files (deduplicated)
    issues_map = load_issues_from_search_files(args.search_files)

    # Load comments from comment files
    comments_map = load_comments_from_files(args.comment_files)

    timeline = []
    issue_meta = {}  # Cache issue metadata

    # Process each issue's changelog
    for issue_key, issue in issues_map.items():
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        issue_type_obj = fields.get("issuetype", {}) or {}
        issue_type = issue_type_obj.get("name", "")
        priority_obj = fields.get("priority", {}) or {}
        priority = priority_obj.get("name", "")

        assignee_obj = fields.get("assignee", {}) or {}
        assignee = assignee_obj.get("displayName", "") or assignee_obj.get("name", "")

        issue_meta[issue_key] = {
            "summary": summary,
            "type": issue_type,
            "priority": priority,
            "assignee": assignee,
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
                    "assignee": assignee,
                    "action": action,
                })

    # Process comments
    for issue_key, comments in comments_map.items():
        meta = issue_meta.get(issue_key, {})
        summary = meta.get("summary", "")
        issue_type = meta.get("type", "")
        priority = meta.get("priority", "")
        assignee = meta.get("assignee", "")

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
                "assignee": assignee,
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
        lines.append("| Time (ET) | Assignee | Issue | Type | Priority | Action |")
        lines.append("|-----------|----------|-------|------|----------|--------|")

        prev_key = None
        for entry in day["entries"]:
            time_str = entry["dt"].strftime("%-I:%M %p")

            if entry["key"] == prev_key:
                # Merge cells — leave assignee/issue/type/priority blank
                lines.append(f"| {time_str} | | | | | {entry['action']} |")
            else:
                type_str = format_type(entry["type"])
                pri_str = format_priority(entry["priority"])
                assignee_str = entry.get("assignee", "")
                issue_link = (
                    f"[{entry['key']}]({JIRA_BASE}/{entry['key']})"
                    f" — {entry['summary']}"
                )
                lines.append(
                    f"| {time_str} | {assignee_str} | {issue_link} | {type_str}"
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
