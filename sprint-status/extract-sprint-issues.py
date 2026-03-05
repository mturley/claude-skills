#!/usr/bin/env python3
"""Extract sprint issues from raw Jira search results for /sprint-status.

Reads raw Jira JSON from stdin (auto-detects format).
Outputs structured sprint data with issues, PR metadata input, and epic keys.

Supports --filter-sprint to keep only issues matching a sprint name keyword.

Uses only Python stdlib. No pip dependencies.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from jira_utils import detect_and_parse_jira, extract_jira_issue, parse_pr_url, parse_sprint, parse_sprint_goal


def main():
    parser = argparse.ArgumentParser(description="Extract sprint issues for /sprint-status")
    parser.add_argument("--filter-sprint", help="Only keep issues with this keyword in sprint name")
    args = parser.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        json.dump({
            "issues": [],
            "pr_metadata_input": [],
            "epic_keys": [],
            "sprint_name": None,
            "sprint_goal": None,
        }, sys.stdout)
        return

    raw_issues = detect_and_parse_jira(raw)
    issues = [extract_jira_issue(i) for i in raw_issues]

    if args.filter_sprint:
        keyword = args.filter_sprint.lower()
        issues = [i for i in issues if i["sprint"] and keyword in i["sprint"].lower()]

    # Extract sprint name and goal from the first matching raw issue
    sprint_name = None
    sprint_goal = None
    for raw_issue in raw_issues:
        sprint_field = raw_issue.get("fields", {}).get("customfield_12310940")
        name = parse_sprint(sprint_field)
        if name and (not args.filter_sprint or args.filter_sprint.lower() in name.lower()):
            sprint_name = name
            sprint_goal = parse_sprint_goal(sprint_field)
            break

    # Collect unique PR metadata input and epic keys
    pr_metadata_input = []
    pr_seen = set()
    epic_keys = set()

    for issue in issues:
        if issue.get("epic"):
            epic_keys.add(issue["epic"])
        for url in issue.get("pr_urls", []):
            parsed = parse_pr_url(url)
            if parsed:
                key = f"{parsed['owner']}/{parsed['repo']}#{parsed['number']}"
                if key not in pr_seen:
                    pr_seen.add(key)
                    pr_metadata_input.append({
                        "owner": parsed["owner"],
                        "repo": parsed["repo"],
                        "number": parsed["number"],
                    })

    json.dump({
        "issues": issues,
        "pr_metadata_input": pr_metadata_input,
        "epic_keys": sorted(epic_keys),
        "sprint_name": sprint_name,
        "sprint_goal": sprint_goal,
    }, sys.stdout)


if __name__ == "__main__":
    main()
