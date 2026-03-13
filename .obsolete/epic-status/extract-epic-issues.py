#!/usr/bin/env python3
"""Extract epic issues from raw Jira search results for /epic-status.

Reads raw Jira JSON from stdin (auto-detects format).
Outputs structured epic data with issues, PR metadata input, and sprint list.

Unlike extract-sprint-issues.py, this script includes sub-tasks and does not
filter by sprint, since an epic spans multiple sprints.

Uses only Python stdlib. No pip dependencies.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from jira_utils import detect_and_parse_jira, extract_jira_issue, parse_pr_url


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        json.dump({
            "issues": [],
            "pr_metadata_input": [],
            "sprints": [],
        }, sys.stdout)
        return

    raw_issues = detect_and_parse_jira(raw)
    issues = [extract_jira_issue(i) for i in raw_issues]

    # Collect unique PR metadata input and sprint names
    pr_metadata_input = []
    pr_seen = set()
    sprints = set()

    for issue in issues:
        if issue.get("sprint"):
            sprints.add(issue["sprint"])
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
        "sprints": sorted(sprints),
    }, sys.stdout)


if __name__ == "__main__":
    main()
