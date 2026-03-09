#!/usr/bin/env python3
"""Render daily activity report from GitHub and Jira data.

Input (stdin JSON): {
  "date": "2026-03-06",
  "github": {"prs_opened": [...], "prs_merged": [...], "reviews": [...]},
  "jira_updated_raw": <raw jira response or null>,
  "jira_crossref_raw": <raw jira response or null>
}

Output (stdout): rendered markdown report

Uses only Python stdlib + shared scripts. No pip dependencies.
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from jira_utils import detect_and_parse_jira, extract_jira_issue, parse_pr_url
from format_utils import format_type, JIRA_BASE


def read_stdin():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)
    return json.loads(raw)


def parse_date_header(date_str):
    """Format date for report header."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%a, %B %-d, %Y")


def build_crossref_map(crossref_raw):
    """Build a map from PR path -> list of extracted Jira issues."""
    if not crossref_raw:
        return {}

    issues = detect_and_parse_jira(crossref_raw)
    pr_to_jira = {}

    for issue in issues:
        extracted = extract_jira_issue(issue)
        for pr_url in extracted["pr_urls"]:
            parsed = parse_pr_url(pr_url)
            if parsed:
                path = f"{parsed['owner']}/{parsed['repo']}/pull/{parsed['number']}"
                if path not in pr_to_jira:
                    pr_to_jira[path] = []
                pr_to_jira[path].append(extracted)

    return pr_to_jira


def build_jira_pr_map(jira_issues):
    """Build a map from Jira key -> list of parsed PR URL objects."""
    jira_to_prs = {}
    for issue in jira_issues:
        prs = []
        for url in issue.get("pr_urls", []):
            parsed = parse_pr_url(url)
            if parsed:
                prs.append(parsed)
        if prs:
            jira_to_prs[issue["key"]] = prs
    return jira_to_prs


def fmt_jira_ref(jira_issue):
    """Format a Jira issue as an inline cross-reference."""
    key = jira_issue["key"]
    type_str = format_type(jira_issue.get("type", ""))
    status = jira_issue.get("status", "")
    return f"[{key}]({JIRA_BASE}/{key}) ({type_str}) {status}"


def fmt_pr_ref(pr, pr_details=None):
    """Format a parsed PR URL as an inline cross-reference, with title if available."""
    path = f"{pr.get('owner', '')}/{pr['repo']}/pull/{pr['number']}" if 'owner' in pr else None
    title = None
    if pr_details and path:
        detail = pr_details.get(path)
        if isinstance(detail, dict):
            title = detail.get("title")
        elif isinstance(detail, str):
            title = detail
    link = f"[{pr['repo']}#{pr['number']}]({pr['url']})"
    if title:
        return f"{link} — {title}"
    return link


REVIEW_STATE_LABEL = {
    "approved": "Approved",
    "changes_requested": "Changes requested",
    "commented": "Commented",
    "dismissed": "Dismissed",
}


def render_pr_section(title, description, prs, crossref_map, show_author=False):
    """Render a section of PRs with Jira cross-references."""
    if not prs:
        return ""

    lines = [f"## {title}", ""]
    if description:
        lines.append(f"*{description}*")
        lines.append("")

    for pr in prs:
        path = f"{pr['repo_full']}/pull/{pr['number']}"

        # Build main line
        link = f"[{pr['repo']}#{pr['number']}]({pr['url']})"
        parts = [f"- {link}"]
        if show_author and pr.get("author"):
            parts.append(f"by @{pr['author']}")
        if pr.get("state"):
            state_label = REVIEW_STATE_LABEL.get(pr["state"], pr["state"])
            parts.append(state_label)
        if pr.get("title"):
            parts.append(pr["title"])
        line = " — ".join(parts)

        lines.append(line)

        # Cross-reference linked Jira issues
        jira_issues = crossref_map.get(path, [])
        for jira in jira_issues:
            lines.append(f"  - {fmt_jira_ref(jira)}")

    lines.append("")
    return "\n".join(lines)


def render_jira_section(jira_issues, jira_pr_map, target_date, pr_titles=None):
    """Render the Jira activity section."""
    if not jira_issues:
        return ""

    lines = ["## Jira Activity", ""]
    lines.append("*Issues where you are assignee or reporter, updated today.*")
    lines.append("")

    sorted_issues = sorted(jira_issues, key=lambda i: i.get("priority_sort", 6))

    for issue in sorted_issues:
        key = issue["key"]
        type_str = format_type(issue.get("type", ""))
        status = issue.get("status", "")
        summary = issue.get("summary", "")
        created = issue.get("created", "")[:10]

        line = f"- [{key}]({JIRA_BASE}/{key}) ({type_str}) — {summary} — **{status}**"
        if created == target_date:
            line += " — *Created today*"
        lines.append(line)

        # Cross-reference linked PRs
        prs = jira_pr_map.get(key, [])
        for pr in prs:
            lines.append(f"  - {fmt_pr_ref(pr, pr_titles)}")

    lines.append("")
    return "\n".join(lines)


def main():
    data = read_stdin()
    target_date = data["date"]
    github = data.get("github", {})
    jira_updated_raw = data.get("jira_updated_raw")
    jira_crossref_raw = data.get("jira_crossref_raw")

    # Parse Jira data
    jira_issues = []
    if jira_updated_raw:
        raw_issues = detect_and_parse_jira(jira_updated_raw)
        for issue in raw_issues:
            extracted = extract_jira_issue(issue)
            # Grab the created date which extract_jira_issue doesn't include
            fields = issue.get("fields", {})
            extracted["created"] = fields.get("created", "")
            jira_issues.append(extracted)

    # Build PR details lookup from fetched details + GitHub event data
    # pr_details maps "owner/repo/pull/number" -> {"title": "...", "author": "..."}
    pr_details = {}
    for path, detail in data.get("pr_details", {}).items():
        if isinstance(detail, dict):
            pr_details[path] = detail
        elif isinstance(detail, str):
            pr_details[path] = {"title": detail, "author": ""}
    # Also index titles from GitHub event data (IssueCommentEvent has full data)
    for pr in (github.get("prs_opened", []) + github.get("prs_merged", []) + github.get("reviews", [])):
        path = f"{pr['repo_full']}/pull/{pr['number']}"
        if path not in pr_details and pr.get("title"):
            pr_details[path] = {"title": pr["title"], "author": pr.get("author", "")}

    # Backfill missing titles/authors into GitHub data from pr_details
    username = data.get("username", "")
    for pr_list in [github.get("prs_opened", []), github.get("prs_merged", []), github.get("reviews", [])]:
        for pr in pr_list:
            path = f"{pr['repo_full']}/pull/{pr['number']}"
            detail = pr_details.get(path, {})
            if not pr.get("title") and detail.get("title"):
                pr["title"] = detail["title"]
            if not pr.get("author") and detail.get("author"):
                pr["author"] = detail["author"]

    # Filter out self-reviews (reviews on own PRs, detectable now that authors are filled)
    reviews = github.get("reviews", [])
    if username:
        reviews = [r for r in reviews if r.get("author", "").lower() != username.lower()]

    # Build cross-reference maps
    crossref_map = build_crossref_map(jira_crossref_raw)
    jira_pr_map = build_jira_pr_map(jira_issues)

    # Render report
    header = f"# Activity — {parse_date_header(target_date)}"
    sections = [header, ""]

    shipped = render_pr_section(
        "Shipped", "PRs merged today.",
        github.get("prs_merged", []), crossref_map
    )
    if shipped:
        sections.append(shipped)

    opened = render_pr_section(
        "Opened", "PRs opened today.",
        github.get("prs_opened", []), crossref_map
    )
    if opened:
        sections.append(opened)

    reviewed = render_pr_section(
        "Reviewed", "Reviews and comments on others' PRs.",
        reviews, crossref_map, show_author=True
    )
    if reviewed:
        sections.append(reviewed)

    jira_section = render_jira_section(jira_issues, jira_pr_map, target_date, pr_details)
    if jira_section:
        sections.append(jira_section)

    # Empty state
    total_gh = len(github.get("prs_merged", [])) + len(github.get("prs_opened", [])) + len(reviews)
    if total_gh == 0 and not jira_issues:
        sections.append("*No activity found for this date.*\n")

    report = "\n".join(sections)
    print(report)


if __name__ == "__main__":
    main()
