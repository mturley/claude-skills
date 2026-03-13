#!/usr/bin/env python3
"""Extract compact Jira fields from raw Jira search responses.

Reads raw Jira JSON from stdin (auto-detects format).
Outputs a compact JSON array with only the fields needed by /reviews-status.

Supported input formats:
  - Raw Jira response: {"success":true,"data":{"issues":[...]}}
  - Tool-result wrapper: [{"type":"text","text":"{\"success\":true,...}"}]
  - Direct issues array: [{"key":"RHOAIENG-51543","fields":{...}}, ...]

Uses only Python stdlib. No pip dependencies.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '.shared-scripts'))
from jira_utils import extract_jira_issue as extract_issue, detect_and_parse_jira as detect_and_parse


def main():
    parser = argparse.ArgumentParser(description="Extract Jira fields for /reviews-status")
    parser.add_argument("--filter-sprint", help="Only keep issues with this keyword in sprint name")
    args = parser.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        json.dump([], sys.stdout)
        return

    issues = detect_and_parse(raw)
    results = [extract_issue(issue) for issue in issues]

    if args.filter_sprint:
        keyword = args.filter_sprint.lower()
        results = [r for r in results if r["sprint"] and keyword in r["sprint"].lower()]

    json.dump(results, sys.stdout)


if __name__ == "__main__":
    main()
