#!/usr/bin/env python3
"""Render the Epic Status markdown report for /epic-status.

Reads assembled epic data as JSON from stdin.
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
    reverse_date, read_stdin,
)
from jira_utils import parse_pr_url

import re

# Status groups in display order. Each entry: (display_name, list_of_jira_statuses)
STATUS_GROUPS = [
    ("Review", ["Review"]),
    ("In Progress", ["In Progress"]),
    ("Backlog", ["New", "To Do", "Backlog"]),
    ("Closed / Resolved", ["Closed", "Resolved"]),
]

DONE_STATUSES = {"Closed", "Resolved"}


def group_issues(issues):
    """Group issues by status category.

    Returns a list of (group_name, issues_list) tuples in display order.
    Only includes non-empty groups. Unknown statuses go to "Other".
    """
    groups = {name: [] for name, _ in STATUS_GROUPS}
    groups["Other"] = []

    status_to_group = {}
    for group_name, statuses in STATUS_GROUPS:
        for s in statuses:
            status_to_group[s] = group_name

    for issue in issues:
        group = status_to_group.get(issue.get("status", ""), "Other")
        groups[group].append(issue)

    result = []
    for name, _ in STATUS_GROUPS:
        if groups[name]:
            result.append((name, groups[name]))
    if groups["Other"]:
        result.append(("Other", groups["Other"]))
    return result


def format_blocked(issue):
    """Format blocked field, hyperlinking any RHOAIENG issue references."""
    if not issue.get("blocked"):
        return "No"
    reason = issue.get("blocked_reason", "")
    if not reason or reason == "None":
        return "Yes"
    text = truncate_title(reason, 30)
    text = re.sub(
        r'(RHOAIENG-\d+)',
        lambda m: f"[{m.group(1)}]({JIRA_BASE}/{m.group(1)})",
        text,
    )
    return f"Yes: {text}"


def render_issue_row(issue, today, pr_lookup, my_jira_username):
    """Render one issue (possibly multiple rows for multi-PR) as markdown table rows.

    All epic tables include State and Sprint columns.
    """
    lines = []
    jira_link = f"[{issue['key']}]({JIRA_BASE}/{issue['key']})"
    issue_type = issue.get("type", "--")
    priority = issue.get("priority", "--")
    sp = str(issue["story_points"]) if issue.get("story_points") is not None else "--"
    orig_sp = str(issue["original_story_points"]) if issue.get("original_story_points") is not None else "--"
    assignee = issue.get("assignee", "") or "--"
    title = truncate_title(issue.get("summary", ""), 40)
    blocked_str = format_blocked(issue)
    reporter = issue.get("reporter", "") or "--"
    updated = format_date(issue.get("updated", ""), today)
    sprint = issue.get("sprint") or "--"
    state = issue.get("status", "--")

    pr_urls = issue.get("pr_urls", [])
    parsed_prs = [p for p in (parse_pr_url(u) for u in pr_urls) if p]
    is_mine = issue.get("assignee_username", "") == my_jira_username

    jira_cols = (
        f"| {jira_link} | {issue_type} | {priority} | {sp} | {orig_sp} "
        f"| {assignee} | {title} | {blocked_str} | {reporter} "
        f"| {updated} | {sprint} | {state}"
    )

    # 12 jira columns (including sprint and state)
    empty_jira = "|  " * 12

    if not parsed_prs:
        lines.append(f"{jira_cols} | -- | -- | -- |")
    else:
        first_pr = parsed_prs[0]
        pr_key = f"{first_pr['owner']}/{first_pr['repo']}#{first_pr['number']}"
        pr_meta = pr_lookup.get(pr_key, {})
        pr_link = format_pr_link(first_pr)
        pr_updated = format_date(pr_meta.get("updated_at", ""), today)
        review_status = pr_meta.get("review_status_mine" if is_mine else "review_status_others", "--")
        lines.append(f"{jira_cols} | {pr_link} | {pr_updated} | {review_status} |")

        for extra_pr in parsed_prs[1:]:
            pr_key = f"{extra_pr['owner']}/{extra_pr['repo']}#{extra_pr['number']}"
            pr_meta = pr_lookup.get(pr_key, {})
            pr_link = format_pr_link(extra_pr)
            pr_updated = format_date(pr_meta.get("updated_at", ""), today)
            review_status = pr_meta.get("review_status_mine" if is_mine else "review_status_others", "--")
            lines.append(f"{empty_jira} {pr_link} | {pr_updated} | {review_status} |")

    return lines


def render_status_table(issues, today, pr_lookup, my_jira_username):
    """Render a single status group as a markdown table.

    All epic tables include Sprint and State columns.
    """
    header = (
        "| Issue | Type | Priority | SP | Orig SP | Assignee | Title "
        "| Blocked | Reporter | Updated | Sprint | State"
        " | PR | PR Updated | Review Status |"
    )
    separator = (
        "|-------|------|----------|----|---------|----------|-------"
        "|---------|----------|---------|--------|------"
        "|----|------------|---------------|"
    )
    lines = [header, separator]

    sorted_issues = sorted(issues, key=lambda i: (
        i.get("priority_sort", 6),
        reverse_date(i.get("updated", "")),
    ))

    for issue in sorted_issues:
        lines.extend(render_issue_row(issue, today, pr_lookup, my_jira_username))

    return lines


def generate_recommendations(issues, pr_lookup, my_github, my_jira_username):
    """Generate prioritized recommended actions.

    Returns list of (text, pr_url_or_none) tuples.
    """
    STATUS_PROXIMITY = {"Review": 0, "In Progress": 1}

    CAT_MY_PR_ACTION = 0
    CAT_REVIEW_NEEDED = 1
    CAT_BLOCKED = 2
    CAT_APPROVED = 3
    CAT_BACKLOG = 4
    CAT_NO_PR = 5

    scored = []

    for issue in issues:
        priority = issue.get("priority_sort", 6)
        status = issue.get("status", "")
        status_prox = STATUS_PROXIMITY.get(status, 3)
        pr_urls = issue.get("pr_urls", [])
        parsed_prs = [parse_pr_url(u) for u in pr_urls if parse_pr_url(u)]
        is_mine = issue.get("assignee_username", "") == my_jira_username
        jira_ref = f"({issue['priority']} \u2014 [{issue['key']}]({JIRA_BASE}/{issue['key']}))"
        title = truncate_title(issue.get("summary", ""), 40)

        # 1. My issues in Review with PR needing attention
        if is_mine and status == "Review":
            for pr in parsed_prs:
                key = f"{pr['owner']}/{pr['repo']}#{pr['number']}"
                meta = pr_lookup.get(key, {})
                rs = meta.get("review_status_mine", "")
                if "**" in rs:
                    if "CI failed" in rs:
                        detail = " \u2014 fix CI and address comments"
                    else:
                        detail = " \u2014 address review comments"
                    scored.append((priority, status_prox, CAT_MY_PR_ACTION,
                        f"Address feedback on [{pr['repo']}#{pr['number']}]({pr['url']}) "
                        f"\"{title}\" {jira_ref}{detail}.",
                        pr["url"]))

        # 2. Teammate issues in Review with PRs needing review
        if not is_mine and status == "Review":
            for pr in parsed_prs:
                key = f"{pr['owner']}/{pr['repo']}#{pr['number']}"
                meta = pr_lookup.get(key, {})
                rs = meta.get("review_status_others", "")
                if "Needs review" in rs or "Needs re-review" in rs:
                    action = "Review" if "Needs review" in rs else "Re-review"
                    conflict = " \u2014 has merge conflicts" if "conflicts" in rs else ""
                    scored.append((priority, status_prox, CAT_REVIEW_NEEDED,
                        f"Unblock {issue.get('assignee', '?')}: {action} "
                        f"[{pr['repo']}#{pr['number']}]({pr['url']}) "
                        f"\"{title}\" {jira_ref}{conflict}.",
                        pr["url"]))

        # 3. Blocked issues (any status)
        if issue.get("blocked") and status not in DONE_STATUSES:
            reason = ""
            if issue.get("blocked_reason") and issue["blocked_reason"] != "None":
                reason = f": {truncate_title(issue['blocked_reason'], 30)}"
            scored.append((priority, status_prox, CAT_BLOCKED,
                f"Blocked{reason} \u2014 [{issue['key']}]({JIRA_BASE}/{issue['key']}) "
                f"\"{title}\" (assigned to {issue.get('assignee', '?')}).",
                None))

        # 4. Approved PRs ready to merge
        if status == "Review":
            for pr in parsed_prs:
                key = f"{pr['owner']}/{pr['repo']}#{pr['number']}"
                meta = pr_lookup.get(key, {})
                rs_mine = meta.get("review_status_mine", "")
                rs_others = meta.get("review_status_others", "")
                if "Approved" in rs_mine or "Approved" in rs_others:
                    scored.append((priority, status_prox, CAT_APPROVED,
                        f"Merge approved [{pr['repo']}#{pr['number']}]({pr['url']}) "
                        f"\"{title}\" {jira_ref}.",
                        pr["url"]))

        # 5. High-priority Backlog items (priority <= Major)
        if status in ("New", "To Do", "Backlog") and priority <= 3:
            scored.append((priority, status_prox, CAT_BACKLOG,
                f"High-priority backlog: [{issue['key']}]({JIRA_BASE}/{issue['key']}) "
                f"\"{title}\" ({issue['priority']}).",
                None))

        # 6. Issues in Review/In Progress with no PR
        if status in ("Review", "In Progress") and not parsed_prs:
            scored.append((priority, status_prox, CAT_NO_PR,
                f"No PR linked: [{issue['key']}]({JIRA_BASE}/{issue['key']}) "
                f"\"{title}\" is {status} but has no PR.",
                None))

    scored.sort(key=lambda t: (t[0], t[1], t[2]))

    if not scored:
        return [("No urgent actions identified. Epic looks good!", None)]

    return [(text, url) for _, _, _, text, url in scored][:10]


def main():
    data = read_stdin()

    today_str = data.get("today", "")
    try:
        today = datetime.strptime(today_str, "%Y-%m-%d").date()
    except ValueError:
        today = date.today()

    epic_key = data.get("epic_key", "N/A")
    epic_summary = data.get("epic_summary", "")
    my_github = data.get("my_github", "")
    my_jira_username = data.get("my_username", "")
    issues = data.get("issues", [])
    pr_metadata_list = data.get("pr_metadata", [])

    # Build PR lookup from metadata
    pr_lookup = {}
    for meta in pr_metadata_list:
        key = f"{meta['owner']}/{meta['repo']}#{meta['number']}"
        pr_lookup[key] = {
            "review_status_mine": meta.get("review_status_mine", "--"),
            "review_status_others": meta.get("review_status_others", "--"),
            "updated_at": meta.get("last_commit_at", ""),
            "state": meta.get("state", ""),
        }

    # Split into my issues and others
    my_issues = [i for i in issues if i.get("assignee_username") == my_jira_username]
    other_issues = [i for i in issues if i.get("assignee_username") != my_jira_username]

    # Compute stats
    total = len(issues)
    total_sp = sum(i.get("story_points", 0) or 0 for i in issues)
    done_sp = sum(i.get("story_points", 0) or 0 for i in issues if i.get("status") in DONE_STATUSES)
    blocked_count = sum(1 for i in issues if i.get("blocked"))
    done_count = sum(1 for i in issues if i.get("status") in DONE_STATUSES)
    sprints = sorted(set(i.get("sprint") for i in issues if i.get("sprint")))
    pct = int(done_sp / total_sp * 100) if total_sp else 0

    # Header
    epic_link = f"[{epic_key}]({JIRA_BASE}/{epic_key})"
    output = [f"# Epic Status: {epic_link} \u2014 {epic_summary}", ""]

    # Summary stats
    output.append(
        f"**{total} issues** ({done_count} done) | "
        f"**{done_sp}/{total_sp} story points** ({pct}%) | "
        f"**{blocked_count} blocked**"
    )
    if sprints:
        output.append(f"**Sprints:** {', '.join(sprints)}")
    output.append("")

    # My assigned issues (single table with State column)
    my_sp = sum(i.get("story_points", 0) or 0 for i in my_issues)
    output.append(f"## My Assigned Issues ({len(my_issues)} issues, {my_sp} story points)")
    output.append("")
    if my_issues:
        output.extend(render_status_table(my_issues, today, pr_lookup, my_jira_username))
    else:
        output.append("_No issues assigned to you in this epic._")
    output.append("")

    # Other epic issues (grouped by status)
    output.append("---")
    output.append("")
    output.append("## Other Epic Issues")
    output.append("")

    groups = group_issues(other_issues)
    for group_name, group_issues_list in groups:
        group_sp = sum(i.get("story_points", 0) or 0 for i in group_issues_list)
        output.append(f"### {group_name} ({len(group_issues_list)} issues, {group_sp} story points)")
        output.append("")
        output.extend(render_status_table(
            group_issues_list, today, pr_lookup, my_jira_username
        ))
        output.append("")

    # Recommendations
    output.append("## Recommended Actions")
    output.append("")
    recs = generate_recommendations(issues, pr_lookup, my_github, my_jira_username)
    for i, (rec, pr_url) in enumerate(recs, 1):
        output.append(f"{i}. {rec}")
        if pr_url:
            output.append(f"   ```")
            output.append(f"   /pr-worktree {pr_url}")
            output.append(f"   ```")
    output.append("")

    print("\n".join(output))


if __name__ == "__main__":
    main()
