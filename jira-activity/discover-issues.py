#!/usr/bin/env python3
"""Discover unique Jira issue keys from multiple search results.

Reads persisted Jira search result files (one per query type) and
deduplicates issue keys. Identifies which issues had user comments.

Usage:
    python3 discover-issues.py \
        --assignee /path/to/assignee.json \
        --watcher /path/to/watcher.json \
        --reporter /path/to/reporter.json \
        --commenter /path/to/commenter.json

Each file should contain a raw Jira searchIssues result (possibly
MCP-wrapped). Missing files are silently skipped.

Uses only Python stdlib. No pip dependencies.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from jira_utils import detect_and_parse_jira


def main():
    parser = argparse.ArgumentParser(description="Discover unique Jira issue keys from search results.")
    parser.add_argument("--assignee", help="Path to assignee search result file")
    parser.add_argument("--watcher", help="Path to watcher search result file")
    parser.add_argument("--reporter", help="Path to reporter search result file")
    parser.add_argument("--commenter", help="Path to commenter search result file")
    args = parser.parse_args()

    all_keys = set()
    commented_keys = set()

    for query_name in ["assignee", "watcher", "reporter", "commenter"]:
        file_path = getattr(args, query_name)
        if not file_path or not os.path.exists(file_path):
            continue

        with open(file_path) as f:
            data = json.load(f)

        issues = detect_and_parse_jira(data)
        for issue in issues:
            key = issue.get("key", "")
            if key:
                all_keys.add(key)
                if query_name == "commenter":
                    commented_keys.add(key)

    result = {
        "issue_keys": sorted(all_keys),
        "commented_keys": sorted(commented_keys),
        "total": len(all_keys),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
