#!/usr/bin/env python3
"""Render a GitHub activity timeline from enriched event data.

Reads JSON from stdin (output of fetch-github-activity.py).
Converts timestamps to target timezone, groups by day, and renders
markdown tables with a summary section.

Usage:
  python3 fetch-github-activity.py | python3 render-github-activity.py [--timezone America/New_York]

Uses only Python stdlib. No pip dependencies.
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from datetime import datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


def parse_iso_datetime(s):
    """Parse ISO datetime string to aware datetime."""
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
        return dt.astimezone(timezone(timedelta(hours=-5)))
    return dt


def format_pr_branch(entry):
    """Format the PR / Branch column for an entry."""
    # PR-linked events
    if entry.get("pr_url") and entry.get("pr_title"):
        short_repo = entry.get("pr_repo", "")
        number = entry.get("pr_number", "")
        title = entry["pr_title"]
        url = entry["pr_url"]
        return f"[{short_repo}#{number}]({url}): *{title}*"

    if entry.get("pr_url") and entry.get("pr_number"):
        short_repo = entry.get("pr_repo", "")
        number = entry.get("pr_number", "")
        url = entry["pr_url"]
        return f"[{short_repo}#{number}]({url})"

    # Issue events (not PRs)
    if entry.get("issue_url"):
        title = entry.get("issue_title", "")
        url = entry["issue_url"]
        number = entry.get("issue_number", "")
        repo = entry.get("repo", "")
        if title:
            return f"[{repo}#{number}]({url}): *{title}*"
        return f"[{repo}#{number}]({url})"

    # Push events without PR
    if entry["type"] == "push":
        owner = entry.get("owner", "")
        repo = entry.get("repo", "")
        branch = entry.get("branch", "")
        return f"`{owner}/{repo}` `{branch}`"

    # Create/delete events
    if entry["type"] in ("create", "delete"):
        owner = entry.get("owner", "")
        repo = entry.get("repo", "")
        ref = entry.get("ref", "")
        ref_type = entry.get("ref_type", "")
        if ref_type == "repository":
            return f"`{owner}/{repo}`"
        return f"`{owner}/{repo}` `{ref}`"

    # Release events
    if entry["type"] == "release":
        owner = entry.get("owner", "")
        repo = entry.get("repo", "")
        return f"`{owner}/{repo}`"

    return ""


def format_action(entry):
    """Format the Action column for an entry."""
    etype = entry["type"]

    if etype == "push":
        sha = entry.get("commit_sha", "")[:7]
        msg = entry.get("commit_message", "") or ""
        url = entry.get("commit_url", "")
        if url and sha:
            return f"Pushed [`{sha}`]({url}) {msg}"
        return f"Pushed `{sha}` {msg}"

    if etype == "pr":
        action = entry.get("action", "")
        action_labels = {
            "opened": "Opened PR",
            "closed": "Closed PR",
            "merged": "Merged",
            "reopened": "Reopened PR",
        }
        return action_labels.get(action, f"PR {action}")

    if etype == "review":
        action = entry.get("action", "")
        comment_count = entry.get("review_comment_count", 0)
        time_start = entry.get("review_time_start")

        if action == "approved":
            result = "Approved"
            if comment_count:
                result += f" ({comment_count} comment{'s' if comment_count != 1 else ''})"
            return result
        elif action == "changes_requested":
            result = "Requested changes"
            if comment_count:
                result += f" ({comment_count} comment{'s' if comment_count != 1 else ''})"
            return result
        elif action == "commented":
            result = "Left review comment"
            return result
        return f"Reviewed ({action})"

    if etype == "review_comment":
        return "Left review comment"

    if etype == "issue_comment":
        return "Commented"

    if etype == "create":
        ref_type = entry.get("ref_type", "")
        ref = entry.get("ref", "")
        if ref_type == "repository":
            return "Created repo"
        elif ref_type == "branch":
            return f"Created branch"
        elif ref_type == "tag":
            return f"Created tag `{ref}`"
        return f"Created {ref_type} `{ref}`"

    if etype == "delete":
        ref_type = entry.get("ref_type", "")
        ref = entry.get("ref", "")
        return f"Deleted {ref_type}"

    if etype == "release":
        action = entry.get("action", "")
        tag = entry.get("tag", "")
        return f"Released `{tag}`"

    return entry.get("action", "")


def render_day_table(day_label, day_entries, today_str, tz_name):
    """Render a single day's table."""
    lines = []

    heading = f"## {day_label}"
    lines.append(heading)
    lines.append("")
    lines.append("| Time | PR / Branch | Action |")
    lines.append("|------|------------|--------|")

    prev_pr_branch = None
    for entry in day_entries:
        dt = entry.get("_dt_local")
        time_str = dt.strftime("%-I:%M %p") if dt else ""

        pr_branch = format_pr_branch(entry)
        action = format_action(entry)

        # Visual merge: blank PR/Branch if same as previous row
        display_pr_branch = pr_branch if pr_branch != prev_pr_branch else ""
        prev_pr_branch = pr_branch

        # Escape pipes in content
        display_pr_branch = display_pr_branch.replace("|", "\\|")
        action = action.replace("|", "\\|")

        lines.append(f"| {time_str} | {display_pr_branch} | {action} |")

    lines.append("")
    return lines


def render_summary(summary):
    """Render the summary section."""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    # PR counts
    lines.append("**Pull Requests:**")
    opened = summary.get("prs_opened", [])
    merged = summary.get("prs_merged", [])
    closed = summary.get("prs_closed", [])
    approved = summary.get("prs_approved", [])
    changes_requested = summary.get("reviews_requested_changes", [])

    if opened:
        lines.append(f"- {len(opened)} opened")
    if merged:
        lines.append(f"- {len(merged)} merged")
    if closed:
        lines.append(f"- {len(closed)} closed (not merged)")
    if approved:
        pr_list = ", ".join(
            f"[{p['repo'].split('/')[-1]}#{p['number']}]({p['url']}): *{p['title']}*"
            for p in approved
        )
        lines.append(f"- {len(approved)} approved ({pr_list})")
    if changes_requested:
        parts = []
        for p in changes_requested:
            cc = p.get("comment_count", 0)
            suffix = f" — {cc} comment{'s' if cc != 1 else ''}" if cc else ""
            parts.append(
                f"[{p['repo'].split('/')[-1]}#{p['number']}]({p['url']}): *{p['title']}*{suffix}"
            )
        lines.append(f"- {len(changes_requested)} review{'s' if len(changes_requested) != 1 else ''} with changes requested ({', '.join(parts)})")
    lines.append("")

    # Repos with commits
    repos = summary.get("repos_with_commits", {})
    if repos:
        lines.append("**Repos with commits pushed:**")
        for repo, count in sorted(repos.items(), key=lambda x: -x[1]):
            lines.append(f"- `{repo}` — {count} commit{'s' if count != 1 else ''}")
        lines.append("")

    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timezone", default="America/New_York")
    args = parser.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)
    events = data.get("events", [])
    summary = data.get("summary", {})
    today_str = data.get("today", "")
    tz_name = args.timezone

    if not events:
        print("No GitHub activity found for the specified time period.")
        return

    # Convert timestamps and sort chronologically
    for entry in events:
        dt = parse_iso_datetime(entry.get("timestamp", ""))
        entry["_dt_local"] = convert_tz(dt, tz_name) if dt else None

    events.sort(key=lambda e: e.get("timestamp", ""))

    # Group by day
    days = OrderedDict()
    for entry in events:
        dt = entry.get("_dt_local")
        if not dt:
            continue
        day_key = dt.strftime("%Y-%m-%d")
        day_name = dt.strftime("%A, %B %-d")
        if day_key not in days:
            days[day_key] = {"label": day_name, "entries": []}
        days[day_key]["entries"].append(entry)

    # Render
    output = []

    for day_key, day in days.items():
        day_lines = render_day_table(
            day["label"], day["entries"], today_str, tz_name
        )
        output.extend(day_lines)

    # Summary
    output.extend(render_summary(summary))

    print("\n".join(output))


if __name__ == "__main__":
    main()
