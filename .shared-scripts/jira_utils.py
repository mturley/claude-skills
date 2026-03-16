#!/usr/bin/env python3
"""Shared Jira utilities for Claude Code skills.

Provides Jira field parsing, response format detection, and PR URL parsing.
Used by /reviews-status and /sprint-status skills.

Uses only Python stdlib. No pip dependencies.

Note: Custom field IDs are for Jira Cloud (redhat.atlassian.net).
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
    """Extract sprint name from customfield_10020.

    Cloud format: list of objects like {"id": 17597, "name": "Dashboard - Green-35", ...}
    Legacy DC format: strings like "com.atlassian.greenhopper.service.sprint.Sprint@...[name=Dashboard - Green-35,...]"

    With shorten=True (default): returns shortened name (e.g. "Green-35").
    With shorten=False: returns the full Jira sprint name (e.g. "Dashboard - Green-35").
    """
    if not sprint_field:
        return None

    # Handle both list and single value
    entries = sprint_field if isinstance(sprint_field, list) else [sprint_field]

    # Take the last entry (most recent sprint)
    last = entries[-1] if entries else None
    if not last:
        return None

    # Cloud format: dict with "name" key
    if isinstance(last, dict):
        name = last.get("name", "")
    # Legacy DC format: string with name=... pattern
    elif isinstance(last, str):
        match = re.search(r"name=([^,\]]+)", last)
        if not match:
            return None
        name = match.group(1).strip()
    else:
        return None

    if not name:
        return None
    if shorten and " - " in name:
        name = name.split(" - ", 1)[1]
    return name


def parse_sprint_goal(sprint_field):
    """Extract sprint goal from customfield_10020.

    Cloud format: list of objects like {"goal": "OCI Storage, MCP Catalog, ...", ...}
    Legacy DC format: strings like "...,goal=OCI Storage, MCP Catalog,...,synced=false,..."
    """
    if not sprint_field:
        return None

    entries = sprint_field if isinstance(sprint_field, list) else [sprint_field]
    last = entries[-1] if entries else None
    if not last:
        return None

    # Cloud format: dict with "goal" key
    if isinstance(last, dict):
        goal = last.get("goal", "")
        return goal.strip() if goal and goal.strip() else None

    # Legacy DC format: string with goal=... pattern
    if isinstance(last, str):
        match = re.search(r"goal=(.*?)(?=,\w+=|\])", last)
        if not match:
            return None
        goal = match.group(1).strip()
        return goal if goal else None

    return None


def parse_pr_urls(pr_field):
    """Extract PR URLs from customfield_10875.

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

    Supports both Cloud and legacy DC field IDs.
    """
    fields = issue.get("fields", {})

    issue_type = fields.get("issuetype", {})
    is_subtask = (issue_type.get("subtask", False) if issue_type else False)
    status = fields.get("status", {})
    priority = fields.get("priority", {})
    priority_name = priority.get("name", "Undefined") if priority else "Undefined"

    # Blocked field: Cloud customfield_10517 or DC customfield_12316543
    blocked_field = fields.get("customfield_10517") or fields.get("customfield_12316543")
    blocked = False
    if blocked_field and isinstance(blocked_field, dict):
        # Cloud uses {"id": "10852"} for True, DC uses {"value": "True"}
        blocked_id = blocked_field.get("id", "")
        blocked_value = blocked_field.get("value", "").lower()
        blocked = str(blocked_id) == "10852" or blocked_value == "true"

    # Assignee and reporter
    assignee_obj = fields.get("assignee") or {}
    reporter_obj = fields.get("reporter") or {}

    # Sprint: Cloud customfield_10020 or DC customfield_12310940
    sprint_field = fields.get("customfield_10020") or fields.get("customfield_12310940")

    # Epic: Cloud customfield_10014 or DC customfield_12311140
    epic = fields.get("customfield_10014") or fields.get("customfield_12311140")

    # PR URLs: Cloud customfield_10875 or DC customfield_12310220
    pr_field = fields.get("customfield_10875") or fields.get("customfield_12310220")

    # Story Points: Cloud customfield_10028 or DC customfield_12310243
    story_points = fields.get("customfield_10028") or fields.get("customfield_12310243")

    # Original Story Points: Cloud customfield_10977 or DC customfield_12314040
    original_story_points = fields.get("customfield_10977") or fields.get("customfield_12314040")

    # Blocked Reason: Cloud customfield_10483 or DC customfield_12316544
    blocked_reason = fields.get("customfield_10483") or fields.get("customfield_12316544")

    # Assignee identifier: Cloud uses accountId, DC used name
    assignee_id = ""
    if assignee_obj:
        assignee_id = assignee_obj.get("accountId", "") or assignee_obj.get("name", "")

    return {
        "key": issue.get("key", ""),
        "summary": fields.get("summary", ""),
        "type": issue_type.get("name", "") if issue_type else "",
        "is_subtask": is_subtask,
        "status": status.get("name", "") if status else "",
        "priority": priority_name,
        "priority_sort": PRIORITY_SORT.get(priority_name, 6),
        "sprint": parse_sprint(sprint_field),
        "epic": epic,
        "pr_urls": parse_pr_urls(pr_field),
        "story_points": story_points,
        "original_story_points": original_story_points,
        "blocked": blocked,
        "blocked_reason": blocked_reason,
        "assignee": assignee_obj.get("displayName", "") if assignee_obj else "",
        "assignee_id": assignee_id,
        "reporter": reporter_obj.get("displayName", "") if reporter_obj else "",
        "updated": fields.get("updated", ""),
    }


def detect_and_parse_jira(data):
    """Auto-detect Jira response format and return a list of issue dicts.

    Supported formats:
      - Tool-result wrapper: [{"type":"text","text":"..."}]
      - Raw Jira response: {"success":true,"data":{"issues":[...]}}
      - Cloud MCP response: {"issues":{"nodes":[...]}}
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
            issues = data.get("issues", {})
            # Cloud MCP format: {"issues": {"nodes": [...]}}
            if isinstance(issues, dict) and "nodes" in issues:
                return issues["nodes"]
            if isinstance(issues, list):
                return issues
            return []
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
    # Self-test with Cloud format
    test_issue_cloud = {
        "key": "RHOAIENG-12345",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Bug"},
            "status": {"name": "In Progress"},
            "priority": {"name": "Major"},
            "customfield_10020": [
                {"id": 17597, "name": "Dashboard - Green-35", "state": "active",
                 "boardId": 1133, "goal": "OCI Storage, MCP Catalog, BoW, tech debt"}
            ],
            "customfield_10014": "RHOAIENG-27992",
            "customfield_10875": "https://github.com/opendatahub-io/odh-dashboard/pull/6466, https://github.com/kubeflow/model-registry/pull/2310",
            "customfield_10028": 5,
            "customfield_10977": 8,
            "customfield_10517": {"id": "10852"},
            "customfield_10483": "Waiting on upstream fix",
            "assignee": {"displayName": "Mike Turley", "accountId": "5a148dfe1121d32de39e72a1"},
            "reporter": {"displayName": "Someone Else", "accountId": "abc123"},
            "updated": "2026-03-04T17:41:50.000+0000",
        },
    }

    result = extract_jira_issue(test_issue_cloud)
    assert result["key"] == "RHOAIENG-12345"
    assert result["sprint"] == "Green-35"
    assert result["blocked"] is True
    assert result["blocked_reason"] == "Waiting on upstream fix"
    assert result["story_points"] == 5
    assert result["original_story_points"] == 8
    assert result["assignee"] == "Mike Turley"
    assert result["assignee_id"] == "5a148dfe1121d32de39e72a1"
    assert result["reporter"] == "Someone Else"
    assert result["pr_urls"] == [
        "https://github.com/opendatahub-io/odh-dashboard/pull/6466",
        "https://github.com/kubeflow/model-registry/pull/2310",
    ]

    # Test parse_sprint with Cloud format and shorten=False
    sprint_field = test_issue_cloud["fields"]["customfield_10020"]
    full_name = parse_sprint(sprint_field, shorten=False)
    assert full_name == "Dashboard - Green-35", f"Got: {full_name}"

    # Test parse_sprint_goal with Cloud format
    goal = parse_sprint_goal(sprint_field)
    assert goal == "OCI Storage, MCP Catalog, BoW, tech debt", f"Got: {goal}"

    # Test with legacy DC format
    test_issue_dc = {
        "key": "RHOAIENG-12345",
        "fields": {
            "summary": "Test issue",
            "issuetype": {"name": "Bug"},
            "status": {"name": "In Progress"},
            "priority": {"name": "Major"},
            "customfield_12310940": [
                "com.atlassian.greenhopper.service.sprint.Sprint@abc[id=82844,rapidViewId=18687,state=ACTIVE,name=Dashboard - Green-35,goal=OCI Storage, MCP Catalog, BoW, tech debt,synced=false]"
            ],
            "customfield_12311140": "RHOAIENG-27992",
            "customfield_12310220": "https://github.com/opendatahub-io/odh-dashboard/pull/6466",
            "customfield_12310243": 5,
            "customfield_12316543": {"value": "True", "id": "12345"},
            "customfield_12316544": "Waiting on upstream fix",
            "assignee": {"displayName": "Mike Turley", "name": "mikejturley"},
            "reporter": {"displayName": "Someone Else", "name": "someone"},
            "updated": "2026-03-04T17:41:50.000+0000",
        },
    }

    result_dc = extract_jira_issue(test_issue_dc)
    assert result_dc["sprint"] == "Green-35"
    assert result_dc["blocked"] is True
    assert result_dc["assignee_id"] == "mikejturley"

    # Test detect_and_parse_jira with Cloud MCP format
    cloud_response = {"issues": {"totalCount": 1, "nodes": [test_issue_cloud]}}
    issues = detect_and_parse_jira(cloud_response)
    assert len(issues) == 1
    assert issues[0]["key"] == "RHOAIENG-12345"

    # Test detect_and_parse_jira with wrapper format
    wrapped = [{"type": "text", "text": json.dumps({"issues": [test_issue_dc]})}]
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

    # Test unblocked issue (Cloud format)
    unblocked_issue = dict(test_issue_cloud)
    unblocked_issue["fields"] = dict(test_issue_cloud["fields"])
    unblocked_issue["fields"]["customfield_10517"] = {"id": "10853"}
    result2 = extract_jira_issue(unblocked_issue)
    assert result2["blocked"] is False

    print("All jira_utils tests passed.")
