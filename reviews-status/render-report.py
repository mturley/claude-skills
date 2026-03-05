#!/usr/bin/env python3
"""Render the PR Dashboard markdown report for /reviews-status.

Reads assembled table data as JSON from stdin.
Outputs complete markdown document to stdout.

Uses only Python stdlib. No pip dependencies.
"""

import json
import sys
from datetime import datetime, date


JIRA_BASE = "https://issues.redhat.com/browse"


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
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
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
    """Format Jira issue as [KEY](url) (Type)."""
    key = jira.get("key", "")
    issue_type = jira.get("type", "")
    return f"[{key}]({JIRA_BASE}/{key}) ({issue_type})"


def format_epic(epic_key, epics):
    """Format epic as [KEY](url) (Short Name)."""
    if not epic_key:
        return "--"
    short_name = epics.get(epic_key, "")
    if short_name:
        return f"[{epic_key}]({JIRA_BASE}/{epic_key}) ({short_name})"
    return f"[{epic_key}]({JIRA_BASE}/{epic_key})"


def sort_key_with_jira(pr):
    """Sort key for Tables 1-3: priority ascending, then updated_at descending."""
    jira_list = pr.get("jira", [])
    if jira_list:
        min_priority = min(j.get("priority_sort", 999) for j in jira_list)
    else:
        min_priority = 999
    updated = pr.get("updated_at", "")
    # Negate updated for descending sort (reverse string comparison via complement)
    return (min_priority, reverse_date(updated))


def reverse_date(iso_str):
    """Return a value that sorts dates in descending order."""
    if not iso_str:
        return ""
    # Invert the string for reverse sort — simple approach:
    # just negate the string by returning its complement
    return "".join(chr(255 - ord(c)) if ord(c) < 256 else c for c in iso_str)


def render_table1(prs, today, epics):
    """Render Table 1: My Open PRs."""
    lines = [
        "## 1: My Open PRs",
        "",
        "| PR | Title | Updated | Review Status | Jira | Priority | Status | Sprint | Epic |",
        "|----|-------|---------|---------------|------|----------|--------|--------|------|",
    ]

    sorted_prs = sorted(prs, key=sort_key_with_jira)

    for pr in sorted_prs:
        pr_link = format_pr_link(pr)
        title = truncate_title(pr.get("title", ""))
        updated = format_date(pr.get("updated_at", ""), today)
        review_status = pr.get("review_status", "--")
        jira_list = pr.get("jira", [])

        if not jira_list:
            lines.append(
                f"| {pr_link} | {title} | {updated} | {review_status} | -- | -- | -- | -- | -- |"
            )
        else:
            first_jira = jira_list[0]
            lines.append(
                f"| {pr_link} | {title} | {updated} | {review_status} "
                f"| {format_jira_link(first_jira)} | {first_jira.get('priority', '--')} "
                f"| {first_jira.get('status', '--')} | {first_jira.get('sprint') or '--'} "
                f"| {format_epic(first_jira.get('epic'), epics)} |"
            )
            for extra_jira in jira_list[1:]:
                lines.append(
                    f"|  |  |  |  "
                    f"| {format_jira_link(extra_jira)} | {extra_jira.get('priority', '--')} "
                    f"| {extra_jira.get('status', '--')} | {extra_jira.get('sprint') or '--'} "
                    f"| {format_epic(extra_jira.get('epic'), epics)} |"
                )

    return lines


def render_table_with_author(prs, today, epics, heading, description=None, important_note=None):
    """Render a table with Author column (Tables 2 and 3)."""
    lines = [heading, ""]
    if description:
        lines.append(description)
        lines.append("")
    lines.extend([
        "| PR | Author | Title | Updated | Review Status | Jira | Priority | Status | Sprint | Epic |",
        "|----|--------|-------|---------|---------------|------|----------|--------|--------|------|",
    ])

    sorted_prs = sorted(prs, key=sort_key_with_jira)

    for pr in sorted_prs:
        pr_link = format_pr_link(pr)
        author = pr.get("author", "--")
        title = truncate_title(pr.get("title", ""))
        updated = format_date(pr.get("updated_at", ""), today)
        review_status = pr.get("review_status", "--")
        jira_list = pr.get("jira", [])

        if not jira_list:
            lines.append(
                f"| {pr_link} | {author} | {title} | {updated} | {review_status} "
                f"| -- | -- | -- | -- | -- |"
            )
        else:
            first_jira = jira_list[0]
            lines.append(
                f"| {pr_link} | {author} | {title} | {updated} | {review_status} "
                f"| {format_jira_link(first_jira)} | {first_jira.get('priority', '--')} "
                f"| {first_jira.get('status', '--')} | {first_jira.get('sprint') or '--'} "
                f"| {format_epic(first_jira.get('epic'), epics)} |"
            )
            for extra_jira in jira_list[1:]:
                lines.append(
                    f"|  |  |  |  |  "
                    f"| {format_jira_link(extra_jira)} | {extra_jira.get('priority', '--')} "
                    f"| {extra_jira.get('status', '--')} | {extra_jira.get('sprint') or '--'} "
                    f"| {format_epic(extra_jira.get('epic'), epics)} |"
                )

    if important_note:
        lines.append("")
        lines.append(important_note)

    return lines


def render_table4(prs, today, people_md_found):
    """Render Table 4: Other Green Scrum PRs with No Jira."""
    lines = ["## 4: Other Green Scrum PRs with No Jira", ""]

    if not people_md_found:
        lines.append(
            "> _Table 4 (Other Green Scrum PRs with No Jira) was excluded because "
            "`.context/people.md` was not found. Run `/populate-people` to generate it._"
        )
        return lines

    lines.extend([
        "| PR | Author | Title | Updated | Review Status |",
        "|----|--------|-------|---------|---------------|",
    ])

    sorted_prs = sorted(prs, key=lambda p: reverse_date(p.get("updated_at", "")))

    for pr in sorted_prs:
        pr_link = format_pr_link(pr)
        author = pr.get("author", "--")
        title = truncate_title(pr.get("title", ""))
        updated = format_date(pr.get("updated_at", ""), today)
        review_status = pr.get("review_status", "--")
        lines.append(f"| {pr_link} | {author} | {title} | {updated} | {review_status} |")

    return lines


def generate_recommendations(table1, table2, table3):
    """Generate prioritized recommendations based on dashboard data."""
    recs = []

    # 1. My PRs with action needed (bold = has **)
    my_action_needed = [
        pr for pr in table1
        if "**" in pr.get("review_status", "")
    ]
    # Prioritize CI failures
    ci_failed = [pr for pr in my_action_needed if "CI failed" in pr.get("review_status", "")]
    ci_ok = [pr for pr in my_action_needed if "CI failed" not in pr.get("review_status", "")]

    for pr in ci_failed:
        jira_text = ""
        jira_list = pr.get("jira", [])
        if jira_list:
            j = jira_list[0]
            jira_text = f" ({j.get('priority', '')} — [{j['key']}]({JIRA_BASE}/{j['key']}))"
        recs.append(
            f"Address comments and fix CI on [{pr['repo']}#{pr['number']}]({pr['url']}){jira_text} — "
            f"CI is failing and reviewers are waiting on your changes."
        )

    for pr in ci_ok:
        jira_text = ""
        jira_list = pr.get("jira", [])
        if jira_list:
            j = jira_list[0]
            jira_text = f" ({j.get('priority', '')} — [{j['key']}]({JIRA_BASE}/{j['key']}))"
        recs.append(
            f"Address review comments on [{pr['repo']}#{pr['number']}]({pr['url']}){jira_text}."
        )

    # 2. Others' PRs needing my review (bold in review_status_others)
    needs_review = [
        pr for pr in table2
        if "**" in pr.get("review_status", "")
    ]
    # Sort by priority
    needs_review.sort(key=lambda p: min(
        (j.get("priority_sort", 999) for j in p.get("jira", [])),
        default=999
    ))

    for pr in needs_review:
        jira_text = ""
        jira_list = pr.get("jira", [])
        if jira_list:
            j = jira_list[0]
            jira_text = f" ({j.get('priority', '')} — [{j['key']}]({JIRA_BASE}/{j['key']}))"
        action = "Review" if "Needs review" in pr.get("review_status", "") else "Re-review"
        conflict_text = " (has merge conflicts)" if "conflicts" in pr.get("review_status", "") else ""
        recs.append(
            f"{action} [{pr['repo']}#{pr['number']}]({pr['url']}) by {pr.get('author', '?')}{jira_text}{conflict_text}."
        )

    # 3. Table 3 high-priority items
    high_priority_t3 = [
        pr for pr in table3
        if any(j.get("priority_sort", 999) <= 3 for j in pr.get("jira", []))
    ]
    for pr in high_priority_t3:
        jira_list = pr.get("jira", [])
        if jira_list:
            j = jira_list[0]
            recs.append(
                f"Consider reviewing [{pr['repo']}#{pr['number']}]({pr['url']}) by {pr.get('author', '?')} — "
                f"{j.get('priority', '')} sprint issue [{j['key']}]({JIRA_BASE}/{j['key']}) in Review."
            )

    # Limit to 6 recommendations
    if not recs:
        recs.append("No urgent actions identified. Dashboard looks good!")

    return recs[:6]


def main():
    data = json.load(sys.stdin)

    today_str = data.get("today", "")
    try:
        today = datetime.strptime(today_str, "%Y-%m-%d").date()
    except ValueError:
        today = date.today()

    sprint_number = data.get("sprint_number", "N")
    excluded_count = data.get("excluded_count", 0)
    people_md_found = data.get("people_md_found", True)
    epics = data.get("epics", {})

    table1 = data.get("table1", [])
    table2 = data.get("table2", [])
    table3 = data.get("table3", [])
    table4 = data.get("table4", [])

    output = ["# PR Dashboard", ""]

    # Table 1
    output.extend(render_table1(table1, today, epics))
    output.append("")

    # Table 2
    output.extend(render_table_with_author(table2, today, epics, "## 2: PRs I'm Reviewing"))
    output.append("")

    # Age filter note
    if excluded_count > 0:
        output.append(f"_{excluded_count} PR(s) excluded because they were last updated over 1 year ago._")
        output.append("")

    # Table 3
    output.extend(render_table_with_author(
        table3, today, epics,
        f"## 3: Other PRs for Green-{sprint_number} Issues in `Review`",
        description=f"_This table shows PRs linked to Green-{sprint_number} Jira issues that are in Review status, excluding those already listed above._",
    ))
    output.append("")

    # Table 4
    output.extend(render_table4(table4, today, people_md_found))
    output.append("")

    # Recommendations
    output.append("## Recommended Actions")
    output.append("")
    recs = generate_recommendations(table1, table2, table3)
    for i, rec in enumerate(recs, 1):
        output.append(f"{i}. {rec}")
    output.append("")

    print("\n".join(output))


if __name__ == "__main__":
    main()
