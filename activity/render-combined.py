#!/usr/bin/env python3
"""Render a combined Jira + GitHub activity timeline.

Reads Jira search results (with expand=changelog), Jira comment files,
and GitHub enriched event JSON (output of fetch-github-activity.py).
Merges all events chronologically and renders a unified markdown timeline.

Usage:
    python3 render-combined.py \
        --github-json /tmp/github-activity.json \
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
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from format_utils import TYPE_EMOJI, PRIORITY_EMOJI, JIRA_BASE
from jira_utils import detect_and_parse_jira

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


# Jira fields to skip (noisy/internal)
SKIP_FIELDS = {"Rank", "Workflow", "RemoteIssueLink"}

MAX_VALUE_LEN = 200


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
    if "New_York" in tz_name or "Eastern" in tz_name:
        return dt.astimezone(timezone(timedelta(hours=-5)))
    return dt


def truncate(s, max_len=MAX_VALUE_LEN):
    if not s or len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


# --- Jira parsing ---

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


def format_jira_action(field, from_str, to_str):
    """Format a Jira changelog item as a readable action string."""
    if field.lower() == "description":
        return "Updated description"
    from_str = truncate(from_str or "")
    to_str = truncate(to_str or "")
    if from_str and to_str:
        return f"**{field}**: {from_str} \u2192 {to_str}"
    elif to_str:
        return f"**{field}**: set to {to_str}"
    elif from_str:
        return f"**{field}**: removed {from_str}"
    else:
        return f"**{field}**: changed"


def load_issues_from_search_files(search_files):
    """Load and deduplicate issues from search result files."""
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
    """Load comments from file paths (ISSUE_KEY=/path/to/file.json)."""
    comments = {}
    for spec in comment_specs:
        if "=" not in spec:
            continue
        issue_key, file_path = spec.split("=", 1)
        if not os.path.exists(file_path):
            continue
        with open(file_path) as f:
            data = json.load(f)
        comments[issue_key] = detect_comments(data)
    return comments


def extract_jira_entries(search_files, comment_specs, username_keys, tz_name, cutoff):
    """Extract timeline entries from Jira data."""
    issues_map = load_issues_from_search_files(search_files)
    comments_map = load_comments_from_files(comment_specs)

    entries = []

    for issue_key, issue in issues_map.items():
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        issue_type = (fields.get("issuetype") or {}).get("name", "")
        priority = (fields.get("priority") or {}).get("name", "")

        type_emoji = TYPE_EMOJI.get(issue_type, "")
        ref_prefix = f"{type_emoji} " if type_emoji else ""
        reference = f"{ref_prefix}[{issue_key}]({JIRA_BASE}/{issue_key}) \u2014 {summary}"

        changelog = issue.get("changelog", {})
        if not changelog:
            continue

        for history in changelog.get("histories", []):
            author = history.get("author", {})
            if author.get("name", "") not in username_keys and author.get("key", "") not in username_keys:
                continue

            dt = parse_iso_datetime(history.get("created", ""))
            if not dt or (cutoff and dt < cutoff):
                continue

            for item in history.get("items", []):
                field = item.get("field", "")
                if field in SKIP_FIELDS:
                    continue

                action = format_jira_action(
                    field, item.get("fromString", ""), item.get("toString", ""),
                )
                dt_local = convert_tz(dt, tz_name)
                entries.append({
                    "dt": dt_local,
                    "source": "jira",
                    "reference": reference,
                    "action": action,
                    "issue_key": issue_key,
                })

    # Comments
    for issue_key, comments in comments_map.items():
        issue = issues_map.get(issue_key, {})
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        issue_type = (fields.get("issuetype") or {}).get("name", "")

        type_emoji = TYPE_EMOJI.get(issue_type, "")
        ref_prefix = f"{type_emoji} " if type_emoji else ""
        reference = f"{ref_prefix}[{issue_key}]({JIRA_BASE}/{issue_key}) \u2014 {summary}"

        for comment in comments:
            author = comment.get("author", {})
            if author.get("name", "") not in username_keys and author.get("key", "") not in username_keys:
                continue

            dt = parse_iso_datetime(comment.get("created", ""))
            if not dt or (cutoff and dt < cutoff):
                continue

            body = comment.get("body", "")
            body_lines = body.strip().split("\n")
            preview = body_lines[0][:200] if body_lines else ""
            if len(body_lines) > 1 or (body_lines and len(body_lines[0]) > 200):
                preview += "..."

            dt_local = convert_tz(dt, tz_name)
            entries.append({
                "dt": dt_local,
                "source": "jira",
                "reference": reference,
                "action": f"**Comment:** \"{preview}\"",
                "issue_key": issue_key,
            })

    return entries


# --- GitHub parsing ---

def format_gh_reference(entry):
    """Format the Reference column for a GitHub entry."""
    prefix = "\U0001f419 "  # octopus emoji

    if entry.get("pr_url") and entry.get("pr_title"):
        short_repo = entry.get("pr_repo", "")
        number = entry.get("pr_number", "")
        return f"{prefix}[{short_repo}#{number}]({entry['pr_url']}): *{entry['pr_title']}*"

    if entry.get("pr_url") and entry.get("pr_number"):
        short_repo = entry.get("pr_repo", "")
        number = entry.get("pr_number", "")
        return f"{prefix}[{short_repo}#{number}]({entry['pr_url']})"

    if entry.get("issue_url"):
        title = entry.get("issue_title", "")
        number = entry.get("issue_number", "")
        repo = entry.get("repo", "")
        if title:
            return f"{prefix}[{repo}#{number}]({entry['issue_url']}): *{title}*"
        return f"{prefix}[{repo}#{number}]({entry['issue_url']})"

    etype = entry.get("type", "")
    owner = entry.get("owner", "")
    repo = entry.get("repo", "")

    if etype == "push":
        branch = entry.get("branch", "")
        return f"{prefix}`{owner}/{repo}` `{branch}`"

    if etype in ("create", "delete"):
        ref = entry.get("ref", "")
        ref_type = entry.get("ref_type", "")
        if ref_type == "repository":
            return f"{prefix}`{owner}/{repo}`"
        return f"{prefix}`{owner}/{repo}` `{ref}`"

    if etype == "release":
        return f"{prefix}`{owner}/{repo}`"

    return prefix


def format_gh_action(entry):
    """Format the Action column for a GitHub entry."""
    etype = entry.get("type", "")

    if etype == "push":
        sha = entry.get("commit_sha", "")[:7]
        msg = entry.get("commit_message", "") or ""
        url = entry.get("commit_url", "")
        if url and sha:
            return f"Pushed [`{sha}`]({url}) {msg}"
        return f"Pushed `{sha}` {msg}"

    if etype == "pr":
        action = entry.get("action", "")
        labels = {"opened": "Opened PR", "closed": "Closed PR", "merged": "Merged", "reopened": "Reopened PR"}
        return labels.get(action, f"PR {action}")

    if etype == "review":
        action = entry.get("action", "")
        cc = entry.get("review_comment_count", 0)
        suffix = f" ({cc} comment{'s' if cc != 1 else ''})" if cc else ""
        if action == "approved":
            return f"Approved{suffix}"
        elif action == "changes_requested":
            return f"Requested changes{suffix}"
        elif action == "commented":
            return "Left review comment"
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
            return "Created branch"
        elif ref_type == "tag":
            return f"Created tag `{ref}`"
        return f"Created {ref_type} `{ref}`"

    if etype == "delete":
        ref_type = entry.get("ref_type", "")
        return f"Deleted {ref_type}"

    if etype == "release":
        tag = entry.get("tag", "")
        return f"Released `{tag}`"

    return entry.get("action", "")


def extract_github_entries(github_json_path, tz_name):
    """Extract timeline entries from GitHub enriched JSON."""
    if not github_json_path or not os.path.exists(github_json_path):
        return [], {}

    with open(github_json_path) as f:
        data = json.load(f)

    events = data.get("events", [])
    summary = data.get("summary", {})
    entries = []

    for event in events:
        dt = parse_iso_datetime(event.get("timestamp", ""))
        if not dt:
            continue

        dt_local = convert_tz(dt, tz_name)
        reference = format_gh_reference(event)
        action = format_gh_action(event)

        entries.append({
            "dt": dt_local,
            "source": "github",
            "reference": reference,
            "action": action,
        })

    return entries, summary


# --- Rendering ---

def render_timeline(jira_entries, github_entries, github_summary, today_str):
    """Render the combined timeline as markdown."""
    all_entries = jira_entries + github_entries
    all_entries.sort(key=lambda x: x["dt"])

    if not all_entries:
        return "No activity found for the specified time period."

    # Group by day
    days = OrderedDict()
    for entry in all_entries:
        day_key = entry["dt"].strftime("%Y-%m-%d")
        day_name = entry["dt"].strftime("%A, %B %-d")
        if day_key not in days:
            days[day_key] = {"label": day_name, "entries": []}
        days[day_key]["entries"].append(entry)

    lines = ["## Combined Activity Timeline", ""]
    lines.append("All times are Eastern Time (ET).")
    lines.append("")

    for day_key, day in days.items():
        heading = f"### {day['label']}"
        if day_key == today_str:
            heading += " (today)"
        lines.append(heading)
        lines.append("")
        lines.append("| Time (ET) | Reference | Action |")
        lines.append("|-----------|-----------|--------|")

        prev_ref = None
        for entry in day["entries"]:
            time_str = entry["dt"].strftime("%-I:%M %p")
            ref = entry["reference"]

            display_ref = ref if ref != prev_ref else ""
            prev_ref = ref

            # Escape pipes in content
            display_ref = display_ref.replace("|", "\\|")
            action = entry["action"].replace("|", "\\|")

            lines.append(f"| {time_str} | {display_ref} | {action} |")

        lines.append("")

    # Summary
    lines.append("---")
    lines.append("")

    # Jira summary
    jira_comment_count = sum(1 for e in jira_entries if e["action"].startswith("**Comment:**"))
    jira_changelog_count = len(jira_entries) - jira_comment_count
    jira_issues = set(e.get("issue_key", "") for e in jira_entries if e.get("issue_key"))

    if jira_entries:
        lines.append(
            f"**Jira:** {jira_changelog_count} changelog action(s)"
            f" + {jira_comment_count} comment(s)"
            f" across {len(jira_issues)} issue(s)."
        )
        lines.append("")

    # GitHub summary
    if github_summary:
        gh_parts = []

        opened = github_summary.get("prs_opened", [])
        merged = github_summary.get("prs_merged", [])
        closed = github_summary.get("prs_closed", [])
        approved = github_summary.get("prs_approved", [])
        changes_requested = github_summary.get("reviews_requested_changes", [])
        repos = github_summary.get("repos_with_commits", {})

        pr_parts = []
        if opened:
            pr_parts.append(f"{len(opened)} opened")
        if merged:
            pr_parts.append(f"{len(merged)} merged")
        if closed:
            pr_parts.append(f"{len(closed)} closed")
        if approved:
            pr_parts.append(f"{len(approved)} approved")
        if changes_requested:
            pr_parts.append(f"{len(changes_requested)} with changes requested")

        if pr_parts:
            gh_parts.append(f"PRs: {', '.join(pr_parts)}")

        if repos:
            total_commits = sum(repos.values())
            repo_count = len(repos)
            gh_parts.append(f"{total_commits} commit(s) across {repo_count} repo(s)")

        if gh_parts:
            lines.append(f"**GitHub:** {'. '.join(gh_parts)}.")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Render combined Jira + GitHub activity timeline.")
    parser.add_argument("--github-json", help="Path to GitHub enriched JSON (output of fetch-github-activity.py)")
    parser.add_argument("--username-keys", nargs="+", default=[],
                        help="Jira username and key variants for the user")
    parser.add_argument("--timezone", default="America/New_York",
                        help="IANA timezone name (default: America/New_York)")
    parser.add_argument("--cutoff", required=True,
                        help="Start date for activity window (YYYY-MM-DD)")
    parser.add_argument("--today", required=True,
                        help="Today's date (YYYY-MM-DD)")
    parser.add_argument("--search-files", nargs="*", default=[],
                        help="Paths to Jira search result files (with expand=changelog)")
    parser.add_argument("--comment-files", nargs="*", default=[],
                        help="Comment file specs as ISSUE_KEY=/path/to/file.json")
    args = parser.parse_args()

    username_keys = set(args.username_keys)
    tz_name = args.timezone

    cutoff = None
    if args.cutoff:
        cutoff = datetime.fromisoformat(args.cutoff + "T00:00:00+00:00")

    # Extract Jira entries
    jira_entries = []
    if args.search_files:
        jira_entries = extract_jira_entries(
            args.search_files, args.comment_files,
            username_keys, tz_name, cutoff,
        )

    # Extract GitHub entries
    github_entries = []
    github_summary = {}
    if args.github_json:
        github_entries, github_summary = extract_github_entries(args.github_json, tz_name)

    # Render
    output = render_timeline(jira_entries, github_entries, github_summary, args.today)
    print(output)


if __name__ == "__main__":
    main()
