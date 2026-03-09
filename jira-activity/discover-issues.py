#!/usr/bin/env python3
"""Discover unique Jira issue keys from multiple search results.

Reads JSON from stdin with raw Jira search results from multiple queries
(assignee, watcher, reporter, commenter). Deduplicates and outputs unique
issue keys, identifying which ones had user comments.

Uses only Python stdlib. No pip dependencies.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from jira_utils import detect_and_parse_jira


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)

    all_keys = set()
    commented_keys = set()

    for query_name in ["assignee", "watcher", "reporter", "commenter"]:
        raw_result = data.get(query_name)
        if not raw_result:
            continue
        issues = detect_and_parse_jira(raw_result)
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
