#!/usr/bin/env python3
"""Fetch open PRs for multiple team members in parallel.

Reads JSON from stdin: {usernames: ["user1", "user2", ...]}
Outputs JSON to stdout: {"user1": [...prs...], "user2": [...], ...}

Uses only Python stdlib. Requires `gh` CLI to be authenticated.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


def fetch_user_prs(username):
    """Run gh search prs for a single user and return (username, results)."""
    result = subprocess.run(
        ["gh", "search", "prs", f"--author={username}", "--state=open",
         "--json", "repository,title,number,url,updatedAt,author",
         "--limit", "100"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"Warning: search for {username} failed: {result.stderr.strip()}",
              file=sys.stderr)
        return username, []
    try:
        return username, json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return username, []


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)
    usernames = data.get("usernames", [])

    if not usernames:
        json.dump({}, sys.stdout)
        return

    results = {}
    with ThreadPoolExecutor(max_workers=min(10, len(usernames))) as pool:
        futures = [pool.submit(fetch_user_prs, u) for u in usernames]
        for future in futures:
            username, prs = future.result()
            results[username] = prs

    json.dump(results, sys.stdout)


if __name__ == "__main__":
    main()
