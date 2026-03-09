#!/usr/bin/env python3
"""Fetch PR details (title, author) from GitHub API in parallel.

The GitHub Events API returns truncated PR objects for PullRequestEvent,
PullRequestReviewEvent, and PullRequestReviewCommentEvent (no title,
html_url, or user). This script fetches the missing details.

Input (stdin JSON): [{"owner": "org", "repo": "name", "number": 123}, ...]
Output (stdout JSON): {"org/name/pull/123": {"title": "...", "author": "..."}, ...}

Uses only Python stdlib + gh CLI. No pip dependencies.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


def read_stdin():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)
    return json.loads(raw)


def fetch_details(pr):
    """Fetch title and author for a single PR via gh api."""
    owner, repo, number = pr["owner"], pr["repo"], pr["number"]
    path = f"{owner}/{repo}/pull/{number}"
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/pulls/{number}",
             "--jq", "{title: .title, author: .user.login}"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip())
            return path, data
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return path, None


def main():
    prs = read_stdin()
    if not prs:
        print("{}")
        return

    details = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_details, pr) for pr in prs]
        for future in futures:
            path, data = future.result()
            if data:
                details[path] = data

    print(json.dumps(details))


if __name__ == "__main__":
    main()
