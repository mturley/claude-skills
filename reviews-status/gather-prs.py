#!/usr/bin/env python3
"""Gather and deduplicate open PRs for /reviews-status.

Runs three `gh search prs` queries in parallel (--author, --reviewed-by,
--commenter), then pipes the results through `assign-tables.py deduplicate`.

Reads JSON from stdin: {my_username, max_age_days, today}
Outputs JSON to stdout: {table1_prs, table2_prs, excluded_count, all_prs, jira_search_paths}

Uses only Python stdlib. Requires `gh` CLI to be authenticated.
"""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


JSON_FIELDS = "repository,title,number,url,updatedAt,author"

SEARCHES = [
    ["gh", "search", "prs", "--author=@me", "--state=open",
     "--json", JSON_FIELDS, "--limit", "100"],
    ["gh", "search", "prs", "--reviewed-by=@me", "--state=open",
     "--json", JSON_FIELDS, "--limit", "100"],
    ["gh", "search", "prs", "--commenter=@me", "--state=open",
     "--json", JSON_FIELDS, "--limit", "100"],
]


def run_search(args):
    """Run a gh search command and return parsed JSON."""
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"Warning: {' '.join(args[:6])} failed: {result.stderr.strip()}",
              file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)

    config = json.loads(raw)

    # Run all 3 searches in parallel
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(run_search, cmd) for cmd in SEARCHES]
        my_prs, reviewed_prs, commented_prs = [f.result() for f in futures]

    # Build input for assign-tables.py deduplicate
    dedup_input = {
        "my_username": config["my_username"],
        "max_age_days": config.get("max_age_days", 365),
        "today": config["today"],
        "my_prs": my_prs,
        "reviewed_prs": reviewed_prs,
        "commented_prs": commented_prs,
    }

    # Call assign-tables.py deduplicate as a subprocess
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assign_script = os.path.join(script_dir, "assign-tables.py")

    result = subprocess.run(
        [sys.executable, assign_script, "deduplicate"],
        input=json.dumps(dedup_input),
        capture_output=True, text=True, timeout=15,
    )

    if result.returncode != 0:
        print(f"Error: assign-tables.py deduplicate failed: {result.stderr.strip()}",
              file=sys.stderr)
        sys.exit(1)

    # Pass through the output
    sys.stdout.write(result.stdout)


if __name__ == "__main__":
    main()
