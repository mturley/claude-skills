#!/usr/bin/env python3
"""Render the PR Dashboard markdown report for /reviews-status.

Reads assembled table data as JSON from stdin.
Outputs complete markdown document to stdout.

Uses only Python stdlib. No pip dependencies.
"""

import json
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from format_utils import (
    JIRA_BASE, truncate_title, format_date, format_pr_link,
    format_jira_link, format_epic, reverse_date, read_stdin,
    format_priority,
)


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
                f"| {format_jira_link(first_jira)} | {format_priority(first_jira.get('priority', ''))} "
                f"| {first_jira.get('status', '--')} | {first_jira.get('sprint') or '--'} "
                f"| {format_epic(first_jira.get('epic'), epics)} |"
            )
            for extra_jira in jira_list[1:]:
                lines.append(
                    f"|  |  |  |  "
                    f"| {format_jira_link(extra_jira)} | {format_priority(extra_jira.get('priority', ''))} "
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
                f"| {format_jira_link(first_jira)} | {format_priority(first_jira.get('priority', ''))} "
                f"| {first_jira.get('status', '--')} | {first_jira.get('sprint') or '--'} "
                f"| {format_epic(first_jira.get('epic'), epics)} |"
            )
            for extra_jira in jira_list[1:]:
                lines.append(
                    f"|  |  |  |  |  "
                    f"| {format_jira_link(extra_jira)} | {format_priority(extra_jira.get('priority', ''))} "
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
    """Generate prioritized recommendations sorted by Jira priority across all categories.

    Returns list of recommendation strings.
    """

    # Category constants for tiebreaking within the same Jira priority:
    # my PRs first, then teammate reviews, then sprint PRs
    CAT_MY_PR = 0
    CAT_TEAMMATE_REVIEW = 1
    CAT_SPRINT_REVIEW = 2

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
        return f" ({format_priority(j.get('priority', ''))} — [{j['key']}]({JIRA_BASE}/{j['key']}))"

    def pr_title(pr):
        return truncate_title(pr.get("title", ""), 45)

    # Build (priority, category, text, pr_url) tuples for all actionable PRs with Jira

    scored = []

    # My PRs needing action
    for pr in table1:
        rs = pr.get("review_status", "")
        if "**" not in rs:
            continue
        title = pr_title(pr)
        if "CI failed" in rs:
            detail = " — fix CI and address feedback"
        elif "Changes requested" in rs:
            detail = " — address requested changes"
        else:
            detail = " — address review comments"
        scored.append((
            jira_priority(pr), CAT_MY_PR,
            f"Unblock your work on [{pr['repo']}#{pr['number']}]({pr['url']}) "
            f"\"{title}\"{jira_ref(pr)}{detail}.",
        ))

    # Reviews I owe teammates WITH Jira
    for pr in table2:
        rs = pr.get("review_status", "")
        if "**" not in rs or not pr.get("jira"):
            continue
        title = pr_title(pr)
        if "Needs approval" in rs:
            action = "Approve"
        elif "Needs review" in rs:
            action = "Review"
        else:
            action = "Re-review"
        conflict = " — has merge conflicts" if "conflicts" in rs else ""
        scored.append((
            jira_priority(pr), CAT_TEAMMATE_REVIEW,
            f"Unblock {pr.get('author', '?')}: {action} [{pr['repo']}#{pr['number']}]({pr['url']}) "
            f"\"{title}\"{jira_ref(pr)}{conflict}.",
        ))

    # Sprint PRs needing review help
    for pr in table3:
        rs = pr.get("review_status", "")
        if "Needs review" not in rs and "Needs re-review" not in rs and "Needs approval" not in rs:
            continue
        title = pr_title(pr)
        if "Needs approval" in rs:
            action = "Approve"
        elif "Needs review" in rs:
            action = "Review"
        else:
            action = "Re-review"
        scored.append((
            jira_priority(pr), CAT_SPRINT_REVIEW,
            f"Help unblock sprint: {action} [{pr['repo']}#{pr['number']}]({pr['url']}) "
            f"\"{title}\" by {pr.get('author', '?')}{jira_ref(pr)}.",
        ))

    # Sort by Jira priority (ascending), then category as tiebreaker
    scored.sort(key=lambda t: (t[0], t[1]))
    recs = [text for _, _, text in scored]

    # Lower-priority items without Jira go at the end

    # Untracked team work (Table 4 non-draft PRs)
    t4_non_draft = [pr for pr in table4 if "Draft" not in pr.get("review_status", "")]
    if t4_non_draft:
        recs.append(
            f"Consider creating Jira tickets for {len(t4_non_draft)} team PR(s) with no linked issue (Table 4)."
        )

    # Reviews I owe WITHOUT Jira
    for pr in table2:
        rs = pr.get("review_status", "")
        if "**" not in rs or pr.get("jira"):
            continue
        title = pr_title(pr)
        if "Needs approval" in rs:
            action = "Approve"
        elif "Needs review" in rs:
            action = "Review"
        else:
            action = "Re-review"
        conflict = " — has merge conflicts" if "conflicts" in rs else ""
        recs.append(
            f"{action} [{pr['repo']}#{pr['number']}]({pr['url']}) "
            f"\"{title}\" by {pr.get('author', '?')}{conflict}."
        )

    if not recs:
        recs.append("No urgent actions identified. Dashboard looks good!")

    return recs[:8]


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
