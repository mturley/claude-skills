#!/usr/bin/env python3
"""Deduplicate PRs and assign them to tables for /reviews-status.

Two subcommands:
  deduplicate  — after Phase 1: normalize, dedup, age-filter, split into Table 1/2
  assign       — after Phase 2: assign Table 3/4 candidates from sprint review + team PRs
                 Accepts raw Jira responses (crossref_raw, sprint_review_raw) and handles
                 extraction internally. Also matches cross-ref Jira to Table 1/2 PRs.

Reads JSON from stdin. Outputs JSON to stdout.
Uses only Python stdlib. No pip dependencies.
"""

import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse


# --- Jira extraction utilities (from extract-jira-fields.py) ---

PRIORITY_SORT = {
    "Blocker": 1,
    "Critical": 2,
    "Major": 3,
    "Normal": 4,
    "Minor": 5,
    "Undefined": 6,
}


def parse_sprint(sprint_field):
    """Extract shortened sprint name from customfield_12310940."""
    if not sprint_field:
        return None
    entries = sprint_field if isinstance(sprint_field, list) else [sprint_field]
    last = entries[-1] if entries else None
    if not last or not isinstance(last, str):
        return None
    match = re.search(r"name=([^,\]]+)", last)
    if not match:
        return None
    name = match.group(1).strip()
    if " - " in name:
        name = name.split(" - ", 1)[1]
    return name


def parse_pr_urls(pr_field):
    """Extract PR URLs from customfield_12310220."""
    if not pr_field:
        return []
    if isinstance(pr_field, list):
        return [u.strip() for u in pr_field if u and u.strip()]
    if isinstance(pr_field, str):
        return [u.strip() for u in pr_field.split(",") if u.strip()]
    return []


def extract_jira_issue(issue):
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


def detect_and_parse_jira(data):
    """Auto-detect Jira response format and return a list of issue dicts."""
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


def normalize_pr(pr):
    """Normalize a gh search PR object to a compact format.

    Input format (from gh search prs --json):
    {
      "repository": {"name": "odh-dashboard", "nameWithOwner": "opendatahub-io/odh-dashboard"},
      "title": "...", "number": 6466, "url": "...",
      "updatedAt": "2026-03-04T17:41:50Z",
      "author": {"login": "mturley"}
    }

    Output format:
    {
      "owner": "opendatahub-io", "repo": "odh-dashboard", "number": 6466,
      "url": "...", "title": "...", "author": "mturley",
      "updated_at": "2026-03-04T17:41:50Z"
    }
    """
    repo_info = pr.get("repository", {})
    name_with_owner = repo_info.get("nameWithOwner", "")
    parts = name_with_owner.split("/", 1)
    owner = parts[0] if len(parts) == 2 else ""
    repo = parts[1] if len(parts) == 2 else repo_info.get("name", "")

    author_info = pr.get("author", {})

    return {
        "owner": owner,
        "repo": repo,
        "number": pr.get("number", 0),
        "url": pr.get("url", ""),
        "title": pr.get("title", ""),
        "author": author_info.get("login", "") if isinstance(author_info, dict) else str(author_info),
        "updated_at": pr.get("updatedAt", ""),
    }


def pr_key(pr):
    """Generate a unique key for a PR (works with normalized format)."""
    return f"{pr['owner']}/{pr['repo']}#{pr['number']}"


def is_too_old(updated_at, today, max_age_days):
    """Check if a PR is older than max_age_days."""
    if not updated_at:
        return False
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        today_dt = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        return (today_dt - dt).days > max_age_days
    except (ValueError, TypeError):
        return False


def generate_jira_path(url):
    """Generate a partial path for Jira cross-reference search.

    Input: "https://github.com/opendatahub-io/odh-dashboard/pull/6466"
    Output: "odh-dashboard/pull/6466"

    Input: "https://github.com/kubeflow/model-registry/pull/2310"
    Output: "kubeflow/model-registry/pull/2310"
    """
    if not url:
        return None
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    # path is like "opendatahub-io/odh-dashboard/pull/6466"
    parts = path.split("/")
    if len(parts) < 4:
        return path
    org, repo = parts[0], parts[1]
    rest = "/".join(parts[2:])  # "pull/6466"
    # For odh-dashboard, strip the org prefix (it's long and redundant)
    if repo == "odh-dashboard":
        return f"{repo}/{rest}"
    return f"{org}/{repo}/{rest}"


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


def cmd_deduplicate(data):
    """Phase 1 → Phase 2 deduplication.

    Input: {my_username, max_age_days, today, my_prs, reviewed_prs, commented_prs}
    Output: {table1_prs, table2_prs, excluded_count, all_prs, jira_search_paths}
    """
    my_username = data["my_username"]
    max_age_days = data.get("max_age_days", 365)
    today = datetime.strptime(data["today"], "%Y-%m-%d").date()

    # Normalize Table 1
    table1 = [normalize_pr(pr) for pr in data.get("my_prs", [])]

    # Merge reviewed + commented, deduplicate
    seen = set()
    merged = []
    for pr in data.get("reviewed_prs", []) + data.get("commented_prs", []):
        norm = normalize_pr(pr)
        key = pr_key(norm)
        if key not in seen:
            seen.add(key)
            merged.append(norm)

    # Remove my own PRs
    merged = [pr for pr in merged if pr["author"] != my_username]

    # Age filter
    excluded_count = 0
    table2 = []
    for pr in merged:
        if is_too_old(pr["updated_at"], today, max_age_days):
            excluded_count += 1
        else:
            table2.append(pr)

    # Combined unique list for metadata fetch
    all_seen = set()
    all_prs = []
    for pr in table1 + table2:
        key = pr_key(pr)
        if key not in all_seen:
            all_seen.add(key)
            all_prs.append({"owner": pr["owner"], "repo": pr["repo"], "number": pr["number"]})

    # Jira search paths
    jira_paths = []
    path_seen = set()
    for pr in table1 + table2:
        path = generate_jira_path(pr["url"])
        if path and path not in path_seen:
            path_seen.add(path)
            jira_paths.append(path)

    return {
        "table1_prs": table1,
        "table2_prs": table2,
        "excluded_count": excluded_count,
        "all_prs": all_prs,
        "jira_search_paths": jira_paths,
    }


def match_crossref_to_prs(crossref_issues, table1_prs, table2_prs):
    """Match batched Jira cross-ref results to Table 1/2 PRs by PR URL.

    Modifies table1_prs and table2_prs in place, adding 'jira' arrays.
    """
    # Build lookup: PR URL → PR dict
    url_to_prs = {}
    for pr in table1_prs + table2_prs:
        url_to_prs[pr["url"]] = pr

    for issue in crossref_issues:
        jira_data = {
            "key": issue["key"],
            "type": issue["type"],
            "priority": issue["priority"],
            "priority_sort": issue["priority_sort"],
            "status": issue["status"],
            "sprint": issue["sprint"],
            "epic": issue.get("epic"),
        }
        for url in issue.get("pr_urls", []):
            url = url.strip()
            if url in url_to_prs:
                pr = url_to_prs[url]
                if "jira" not in pr:
                    pr["jira"] = []
                pr["jira"].append(jira_data)


def cmd_assign(data):
    """Phase 2 → Phase 3 table assignment.

    Input (new format with raw Jira):
      {my_username, max_age_days, today, table1_prs, table2_prs,
       crossref_raw, sprint_review_raw, filter_sprint, team_prs}

    Input (legacy format with pre-extracted Jira):
      {my_username, max_age_days, today, table1_prs, table2_prs,
       sprint_review_issues, team_prs}

    Output: {table1_prs, table2_prs, table3_candidates, table4_candidates,
             metadata_input, epic_keys, table4_jira_paths}
    """
    my_username = data["my_username"]
    max_age_days = data.get("max_age_days", 365)
    today = datetime.strptime(data["today"], "%Y-%m-%d").date()

    table1_prs = data.get("table1_prs", [])
    table2_prs = data.get("table2_prs", [])

    # --- Handle cross-ref Jira (raw or skip) ---
    if "crossref_raw" in data:
        raw_issues = detect_and_parse_jira(data["crossref_raw"])
        crossref_extracted = [extract_jira_issue(i) for i in raw_issues]
        match_crossref_to_prs(crossref_extracted, table1_prs, table2_prs)

    # --- Handle sprint review Jira (raw or pre-extracted) ---
    if "sprint_review_raw" in data:
        raw_issues = detect_and_parse_jira(data["sprint_review_raw"])
        sprint_issues = [extract_jira_issue(i) for i in raw_issues]
        filter_sprint = data.get("filter_sprint")
        if filter_sprint:
            keyword = filter_sprint.lower()
            sprint_issues = [
                i for i in sprint_issues
                if i["sprint"] and keyword in i["sprint"].lower()
            ]
    else:
        sprint_issues = data.get("sprint_review_issues", [])

    # Build set of Table 1+2 PR keys for dedup
    existing_keys = set()
    for pr in table1_prs + table2_prs:
        existing_keys.add(pr_key(pr))

    # Process sprint review issues → Table 3 candidates
    table3 = []
    table3_keys = set()

    for issue in sprint_issues:
        pr_urls = issue.get("pr_urls", [])
        jira_data = {
            "key": issue.get("key", ""),
            "type": issue.get("type", ""),
            "priority": issue.get("priority", ""),
            "priority_sort": issue.get("priority_sort", 6),
            "status": issue.get("status", ""),
            "sprint": issue.get("sprint", ""),
            "epic": issue.get("epic"),
        }

        for url in pr_urls:
            parsed = parse_pr_url(url)
            if not parsed:
                continue
            key = f"{parsed['owner']}/{parsed['repo']}#{parsed['number']}"
            if key in existing_keys or key in table3_keys:
                continue
            table3_keys.add(key)
            table3.append({
                "owner": parsed["owner"],
                "repo": parsed["repo"],
                "number": parsed["number"],
                "url": parsed["url"],
                "title": "",  # Will be filled by metadata fetch
                "author": "",  # Will be filled by metadata fetch
                "updated_at": "",  # Will be filled by metadata fetch
                "jira": jira_data,
            })

    # Build full exclusion set (Table 1+2+3)
    all_existing_keys = existing_keys | table3_keys

    # Process team PRs → Table 4 candidates
    team_prs = data.get("team_prs", {})
    table4 = []
    table4_keys = set()

    for username, prs in team_prs.items():
        for pr in prs:
            norm = normalize_pr(pr)
            key = pr_key(norm)
            if key in all_existing_keys or key in table4_keys:
                continue
            if is_too_old(norm["updated_at"], today, max_age_days):
                continue
            # Skip my own PRs
            if norm["author"] == my_username:
                continue
            table4_keys.add(key)
            table4.append(norm)

    # Metadata input for fetch-pr-metadata.py
    metadata_input = []
    meta_seen = set()
    for pr in table3 + table4:
        key = f"{pr['owner']}/{pr['repo']}#{pr['number']}"
        if key not in meta_seen:
            meta_seen.add(key)
            metadata_input.append({"owner": pr["owner"], "repo": pr["repo"], "number": pr["number"]})

    # Collect unique epic keys
    epic_keys = list({issue["epic"] for issue in sprint_issues if issue.get("epic")})

    # Jira paths for Table 4 checks
    table4_jira_paths = []
    for pr in table4:
        path = generate_jira_path(pr["url"])
        if path:
            table4_jira_paths.append(path)

    return {
        "table1_prs": table1_prs,
        "table2_prs": table2_prs,
        "table3_candidates": table3,
        "table4_candidates": table4,
        "metadata_input": metadata_input,
        "epic_keys": epic_keys,
        "table4_jira_paths": table4_jira_paths,
    }


def read_stdin():
    """Read and parse JSON from stdin with clear error messages."""
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin. Pipe JSON data to this script.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("deduplicate", "assign"):
        print("Usage: assign-tables.py <deduplicate|assign>", file=sys.stderr)
        sys.exit(1)

    subcommand = sys.argv[1]
    data = read_stdin()

    if subcommand == "deduplicate":
        result = cmd_deduplicate(data)
    else:
        result = cmd_assign(data)

    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
