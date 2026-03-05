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
import re
import sys

PRIORITY_SORT = {
    "Blocker": 1,
    "Critical": 2,
    "Major": 3,
    "Normal": 4,
    "Minor": 5,
    "Undefined": 6,
}


def parse_sprint(sprint_field):
    """Extract shortened sprint name from customfield_12310940.

    The field contains strings like:
      com.atlassian.greenhopper.service.sprint.Sprint@...[id=82844,...,name=Dashboard - Green-35,...]

    Returns the last sprint's name, shortened (e.g. "Dashboard - Green-35" -> "Green-35").
    """
    if not sprint_field:
        return None

    # Handle both list and single string
    entries = sprint_field if isinstance(sprint_field, list) else [sprint_field]

    # Take the last entry (most recent sprint)
    last = entries[-1] if entries else None
    if not last or not isinstance(last, str):
        return None

    match = re.search(r"name=([^,\]]+)", last)
    if not match:
        return None

    name = match.group(1).strip()
    # Shorten: "Dashboard - Green-35" -> "Green-35"
    if " - " in name:
        name = name.split(" - ", 1)[1]
    return name


def parse_pr_urls(pr_field):
    """Extract PR URLs from customfield_12310220.

    The field can be a string (comma-separated URLs) or a list.
    """
    if not pr_field:
        return []
    if isinstance(pr_field, list):
        return [u.strip() for u in pr_field if u and u.strip()]
    if isinstance(pr_field, str):
        return [u.strip() for u in pr_field.split(",") if u.strip()]
    return []


def extract_issue(issue):
    """Extract compact fields from a single Jira issue."""
    fields = issue.get("fields", {})

    issue_type = fields.get("issuetype", {})
    status = fields.get("status", {})
    priority = fields.get("priority", {})
    priority_name = priority.get("name", "Undefined") if priority else "Undefined"

    return {
        "key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "type": issue_type.get("name", "") if issue_type else "",
        "status": status.get("name", "") if status else "",
        "priority": priority_name,
        "priority_sort": PRIORITY_SORT.get(priority_name, 6),
        "sprint": parse_sprint(fields.get("customfield_12310940")),
        "epic": fields.get("customfield_12311140"),
        "pr_urls": parse_pr_urls(fields.get("customfield_12310220")),
    }


def detect_and_parse(raw):
    """Auto-detect input format and return a list of Jira issue dicts."""
    data = json.loads(raw) if isinstance(raw, str) else raw

    # Format 1: Tool-result wrapper [{"type":"text","text":"..."}]
    if isinstance(data, list) and data and isinstance(data[0], dict) and "type" in data[0] and "text" in data[0]:
        inner = json.loads(data[0]["text"])
        return detect_and_parse(inner)

    # Format 2: Raw Jira response {"success":true,"data":{"issues":[...]}}
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict):
            return data["data"].get("issues", [])
        if "issues" in data:
            return data.get("issues", [])
        # Single issue
        if "key" in data and "fields" in data:
            return [data]
        return []

    # Format 3: Direct issues array [{"key":"...","fields":{...}}, ...]
    if isinstance(data, list):
        return data

    return []


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
