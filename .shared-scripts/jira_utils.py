#!/usr/bin/env python3
"""Shared Jira utilities for Claude Code skills.

Provides Jira field parsing, response format detection, and PR URL parsing.
Used by /reviews-status and /sprint-status skills.

Uses only Python stdlib. No pip dependencies.
"""

import json
import re
from urllib.parse import urlparse


PRIORITY_SORT = {
    "Blocker": 1,
    "Critical": 2,
    "Major": 3,
    "Normal": 4,
    "Minor": 5,
    "Undefined": 6,
}


def parse_sprint(sprint_field, shorten=True):
    """Extract sprint name from customfield_12310940.

    The field contains strings like:
      com.atlassian.greenhopper.service.sprint.Sprint@...[id=82844,...,name=Dashboard - Green-35,...]

    With shorten=True (default): returns shortened name (e.g. "Green-35").
    With shorten=False: returns the full Jira sprint name (e.g. "Dashboard - Green-35").
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
    if shorten and " - " in name:
        name = name.split(" - ", 1)[1]
    return name


def parse_sprint_goal(sprint_field):
    """Extract sprint goal from customfield_12310940.

    The field contains strings like:
      ...,goal=OCI Storage, MCP Catalog, BoW, tech debt,synced=false,...

    Returns the goal text, or None if not found.
    """
    if not sprint_field:
        return None

    entries = sprint_field if isinstance(sprint_field, list) else [sprint_field]
    last = entries[-1] if entries else None
    if not last or not isinstance(last, str):
        return None

    match = re.search(r"goal=(.*?)(?=,\w+=|\])", last)
    if not match:
        return None

    goal = match.group(1).strip()
    return goal if goal else None


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


def extract_jira_issue(issue):
    """Extract compact fields from a single Jira issue.

    Returns a dict with all fields needed by both /reviews-status and /sprint-status.
    Consumers use only the keys they need; extra keys are harmless.
    """
    fields = issue.get("fields", {})

    issue_type = fields.get("issuetype", {})
    is_subtask = (issue_type.get("subtask", False) if issue_type else False)
    status = fields.get("status", {})
    priority = fields.get("priority", {})
    priority_name = priority.get("name", "Undefined") if priority else "Undefined"

    # Blocked field: customfield_12316543 is a select with {"value": "True/False"}
    blocked_field = fields.get("customfield_12316543")
    blocked = False
    if blocked_field and isinstance(blocked_field, dict):
        blocked = blocked_field.get("value", "").lower() == "true"

    # Assignee and reporter
    assignee_obj = fields.get("assignee") or {}
    reporter_obj = fields.get("reporter") or {}

    return {
        "key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "type": issue_type.get("name", "") if issue_type else "",
        "is_subtask": is_subtask,
        "status": status.get("name", "") if status else "",
        "priority": priority_name,
        "priority_sort": PRIORITY_SORT.get(priority_name, 6),
        "sprint": parse_sprint(fields.get("customfield_12310940")),
        "epic": fields.get("customfield_12311140"),
        "pr_urls": parse_pr_urls(fields.get("customfield_12310220")),
        "story_points": fields.get("customfield_12310243"),
        "original_story_points": fields.get("customfield_12314040"),
        "blocked": blocked,
        "blocked_reason": fields.get("customfield_12316544"),
        "assignee": assignee_obj.get("displayName", "") if assignee_obj else "",
        "assignee_username": assignee_obj.get("name", "") if assignee_obj else "",
        "reporter": reporter_obj.get("displayName", "") if reporter_obj else "",
        "updated": fields.get("updated", ""),
    }


def detect_and_parse_jira(data):
    """Auto-detect Jira response format and return a list of issue dicts.

    Supported formats:
      - Tool-result wrapper: [{"type":"text","text":"..."}]
      - Raw Jira response: {"success":true,"data":{"issues":[...]}}
      - Direct issues array: [{"key":"...","fields":{...}}, ...]
    """
    if isinstance(data, str):
        data = json.loads(data)
    # Tool-result wrapper [{"type":"text","text":"..."}]
    if isinstance(data, list) and data and isinstance(data[0], dict) and "type" in data[0] and "text" in data[0]:
        inner = json.loads(data[0]["text"])
        return detect_and_parse_jira(inner)
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict):
            return data["data"].get("issues", [])
        if "issues" in data:
            return data.get("issues", [])
        if "key" in data and "fields" in data:
            return [data]
        return []
    if isinstance(data, list):
        return data
    return []


def parse_pr_url(url):
    """Parse a GitHub PR URL into {owner, repo, number, url}.

    Returns None for non-GitHub or invalid URLs.
    """
    if not url or "github.com" not in url:
        return None
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    # Expected: ["org", "repo", "pull", "number"]
    if len(parts) < 4 or parts[2] != "pull":
        return None
    try:
        number = int(parts[3])
    except (ValueError, IndexError):
        return None
    return {
        "owner": parts[0],
        "repo": parts[1],
        "number": number,
        "url": url,
    }


if __name__ == "__main__":
    # Self-test
    test_issue = {
        "key": "RHOAIENG-12345",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Bug"},
            "status": {"name": "In Progress"},
            "priority": {"name": "Major"},
            "customfield_12310940": [
                "com.atlassian.greenhopper.service.sprint.Sprint@abc[id=82844,rapidViewId=18687,state=ACTIVE,name=Dashboard - Green-35,startDate=2026-03-02T14:39:00.000Z,endDate=2026-03-23T14:39:00.000Z,completeDate=<null>,activatedDate=2026-03-02T15:26:30.540Z,sequence=82844,goal=OCI Storage, MCP Catalog, BoW, tech debt,synced=false,autoStartStop=false,incompleteIssuesDestinationId=<null>]"
            ],
            "customfield_12311140": "RHOAIENG-27992",
            "customfield_12310220": "https://github.com/opendatahub-io/odh-dashboard/pull/6466, https://github.com/kubeflow/model-registry/pull/2310",
            "customfield_12310243": 5,
            "customfield_12314040": 8,
            "customfield_12316543": {"value": "True", "id": "12345"},
            "customfield_12316544": "Waiting on upstream fix",
            "assignee": {"displayName": "Mike Turley", "name": "mikejturley"},
            "reporter": {"displayName": "Someone Else", "name": "someone"},
            "updated": "2026-03-04T17:41:50.000+0000",
        },
    }

    result = extract_jira_issue(test_issue)
    assert result["key"] == "RHOAIENG-12345"
    assert result["sprint"] == "Green-35"
    assert result["blocked"] is True
    assert result["blocked_reason"] == "Waiting on upstream fix"
    assert result["story_points"] == 5
    assert result["original_story_points"] == 8
    assert result["assignee"] == "Mike Turley"
    assert result["assignee_username"] == "mikejturley"
    assert result["reporter"] == "Someone Else"
    assert result["pr_urls"] == [
        "https://github.com/opendatahub-io/odh-dashboard/pull/6466",
        "https://github.com/kubeflow/model-registry/pull/2310",
    ]

    # Test parse_sprint with shorten=False
    sprint_field = test_issue["fields"]["customfield_12310940"]
    full_name = parse_sprint(sprint_field, shorten=False)
    assert full_name == "Dashboard - Green-35", f"Got: {full_name}"

    # Test parse_sprint_goal
    goal = parse_sprint_goal(sprint_field)
    assert goal == "OCI Storage, MCP Catalog, BoW, tech debt", f"Got: {goal}"

    # Test detect_and_parse_jira with wrapper format
    wrapped = [{"type": "text", "text": json.dumps({"issues": [test_issue]})}]
    issues = detect_and_parse_jira(wrapped)
    assert len(issues) == 1
    assert issues[0]["key"] == "RHOAIENG-12345"

    # Test parse_pr_url
    parsed = parse_pr_url("https://github.com/opendatahub-io/odh-dashboard/pull/6466")
    assert parsed == {
        "owner": "opendatahub-io",
        "repo": "odh-dashboard",
        "number": 6466,
        "url": "https://github.com/opendatahub-io/odh-dashboard/pull/6466",
    }
    assert parse_pr_url("not-a-github-url") is None
    assert parse_pr_url(None) is None

    # Test unblocked issue
    unblocked_issue = dict(test_issue)
    unblocked_issue["fields"] = dict(test_issue["fields"])
    unblocked_issue["fields"]["customfield_12316543"] = {"value": "False", "id": "99"}
    result2 = extract_jira_issue(unblocked_issue)
    assert result2["blocked"] is False

    print("All jira_utils tests passed.")
