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

    lines.append(
        f"_Open PRs from Green Scrum members with no linked RHOAIENG Jira issue."
        f" Consider creating tickets or linking existing ones._"
    )
    lines.append("")
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


def generate_recommendations(table1, table2, table3, table4):
    """Generate prioritized recommendations focused on unblocking the Green Scrum."""
    recs = []

    def jira_priority(pr):
        return min(
            (j.get("priority_sort", 999) for j in pr.get("jira", [])),
            default=999,
        )

    def jira_ref(pr):
        jira_list = pr.get("jira", [])
        if not jira_list:
            return ""
        j = jira_list[0]
        return f" ({j.get('priority', '')} — [{j['key']}]({JIRA_BASE}/{j['key']}))"

    # 1. Reviews I owe teammates WITH Jira (I'm blocking sprint work)
    t2_with_jira = [
        pr for pr in table2
        if "**" in pr.get("review_status", "") and pr.get("jira")
    ]
    t2_with_jira.sort(key=jira_priority)

    for pr in t2_with_jira:
        action = "Review" if "Needs review" in pr.get("review_status", "") else "Re-review"
        conflict = " — has merge conflicts" if "conflicts" in pr.get("review_status", "") else ""
        recs.append(
            f"Unblock {pr.get('author', '?')}: {action} [{pr['repo']}#{pr['number']}]({pr['url']})"
            f"{jira_ref(pr)}{conflict}."
        )

    # 2. My PRs needing action (blocking my own sprint work from landing)
    my_action = [pr for pr in table1 if "**" in pr.get("review_status", "")]
    my_action.sort(key=jira_priority)

    for pr in my_action:
        if "CI failed" in pr.get("review_status", ""):
            detail = " — fix CI and address comments"
        else:
            detail = " — address review comments"
        recs.append(
            f"Unblock your work on [{pr['repo']}#{pr['number']}]({pr['url']})"
            f"{jira_ref(pr)}{detail}."
        )

    # 3. Sprint PRs needing review help (Table 3 with "Needs review" or "Needs re-review")
    t3_needs_review = [
        pr for pr in table3
        if "Needs review" in pr.get("review_status", "")
        or "Needs re-review" in pr.get("review_status", "")
    ]
    t3_needs_review.sort(key=jira_priority)

    for pr in t3_needs_review:
        recs.append(
            f"Help unblock sprint: Review [{pr['repo']}#{pr['number']}]({pr['url']}) by "
            f"{pr.get('author', '?')}{jira_ref(pr)}."
        )

    # 4. Untracked team work (Table 4 non-draft PRs)
    t4_non_draft = [pr for pr in table4 if "Draft" not in pr.get("review_status", "")]
    if t4_non_draft:
        recs.append(
            f"Consider creating Jira tickets for {len(t4_non_draft)} team PR(s) with no linked issue (Table 4)."
        )

    # 5. Reviews I owe WITHOUT Jira (lower priority)
    t2_no_jira = [
        pr for pr in table2
        if "**" in pr.get("review_status", "") and not pr.get("jira")
    ]
    for pr in t2_no_jira:
        action = "Review" if "Needs review" in pr.get("review_status", "") else "Re-review"
        conflict = " — has merge conflicts" if "conflicts" in pr.get("review_status", "") else ""
        recs.append(
            f"{action} [{pr['repo']}#{pr['number']}]({pr['url']}) by {pr.get('author', '?')}{conflict}."
        )

    if not recs:
        recs.append("No urgent actions identified. Dashboard looks good!")

    return recs[:8]


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


def main():
    data = read_stdin()

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
    recs = generate_recommendations(table1, table2, table3, table4)
    for i, rec in enumerate(recs, 1):
        output.append(f"{i}. {rec}")
    output.append("")

    print("\n".join(output))


if __name__ == "__main__":
    main()
