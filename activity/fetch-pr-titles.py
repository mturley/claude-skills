#!/usr/bin/env python3
"""Fetch PR titles from GitHub API in parallel.

Input (stdin JSON): [{"owner": "org", "repo": "name", "number": 123}, ...]
Output (stdout JSON): {"org/name/pull/123": "PR title", ...}

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


def fetch_title(pr):
    """Fetch a single PR title via gh api."""
    owner, repo, number = pr["owner"], pr["repo"], pr["number"]
    path = f"{owner}/{repo}/pull/{number}"
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}/pulls/{number}", "--jq", ".title"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            return path, result.stdout.strip()
    except subprocess.TimeoutExpired:
        pass
    return path, ""


def main():
    prs = read_stdin()
    if not prs:
        print("{}")
        return

    titles = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_title, pr) for pr in prs]
        for future in futures:
            path, title = future.result()
            if title:
                titles[path] = title

    print(json.dumps(titles))


if __name__ == "__main__":
    main()
