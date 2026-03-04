#!/usr/bin/env python3
"""Fetch GitHub PR metadata in parallel.

Reads a JSON array of {owner, repo, number} objects from stdin.
Outputs a JSON array with metadata for each PR:
  state, draft, labels, mergeable_state, review_count, last_review_at,
  last_commit_at, ci_status

Uses only Python stdlib. Requires `gh` CLI to be authenticated.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_gh(args):
    """Run a gh command and return parsed JSON or raw stdout."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True, text=True, timeout=30
    )
    return result.stdout, result.stderr, result.returncode


def fetch_pr_info(owner, repo, number):
    """Fetch PR info (labels, draft, mergeable_state)."""
    stdout, _, rc = run_gh([
        "api", f"repos/{owner}/{repo}/pulls/{number}",
        "--jq", '{draft, mergeable_state, labels: [.labels[].name], state}'
    ])
    if rc != 0 or not stdout.strip():
        return None
    return json.loads(stdout)


def fetch_reviews(owner, repo, number):
    """Fetch review count and last review timestamp."""
    stdout, _, rc = run_gh([
        "api", f"repos/{owner}/{repo}/pulls/{number}/reviews",
        "--jq", '{count: length, last_review_at: (sort_by(.submitted_at) | last | .submitted_at)}'
    ])
    if rc != 0 or not stdout.strip():
        return {"count": 0, "last_review_at": None}
    return json.loads(stdout)


def fetch_last_commit(owner, repo, number):
    """Fetch last commit timestamp."""
    stdout, _, rc = run_gh([
        "api", f"repos/{owner}/{repo}/pulls/{number}/commits",
        "--jq", 'last | .commit.committer.date'
    ])
    if rc != 0 or not stdout.strip():
        return None
    return stdout.strip().strip('"')


def fetch_ci_status(owner, repo, number):
    """Fetch CI status from gh pr checks."""
    stdout, _, rc = run_gh([
        "pr", "checks", str(number), "--repo", f"{owner}/{repo}"
    ])
    if rc != 0 and not stdout.strip():
        return "N/A"
    lines = stdout.strip().split("\n") if stdout.strip() else []
    if not lines:
        return "N/A"
    has_fail = any("fail" in line.lower() for line in lines)
    has_pending = any("pending" in line.lower() for line in lines)
    if has_fail:
        return "Failed"
    if has_pending:
        return "Running"
    # Check if all passed
    has_pass = any("pass" in line.lower() or "success" in line.lower() for line in lines)
    if has_pass:
        return "Passed"
    return "N/A"


def fetch_one_pr(pr):
    """Fetch all metadata for a single PR."""
    owner = pr["owner"]
    repo = pr["repo"]
    number = pr["number"]

    # First fetch PR info (we need it for state/draft/labels)
    info = fetch_pr_info(owner, repo, number)
    if info is None:
        return {
            "owner": owner, "repo": repo, "number": number,
            "error": "Failed to fetch PR info"
        }

    # Then fetch reviews, commits, and CI in parallel
    with ThreadPoolExecutor(max_workers=3) as inner:
        review_future = inner.submit(fetch_reviews, owner, repo, number)
        commit_future = inner.submit(fetch_last_commit, owner, repo, number)
        ci_future = inner.submit(fetch_ci_status, owner, repo, number)

        reviews = review_future.result()
        last_commit_at = commit_future.result()
        ci_status = ci_future.result()

    return {
        "owner": owner,
        "repo": repo,
        "number": number,
        "state": info.get("state", "unknown"),
        "draft": info.get("draft", False),
        "labels": info.get("labels", []),
        "mergeable_state": info.get("mergeable_state", "unknown"),
        "review_count": reviews.get("count", 0),
        "last_review_at": reviews.get("last_review_at"),
        "last_commit_at": last_commit_at,
        "ci_status": ci_status,
    }


def main():
    input_data = json.load(sys.stdin)
    if not input_data:
        json.dump([], sys.stdout)
        return

    results = []
    with ThreadPoolExecutor(max_workers=min(30, len(input_data) * 4)) as pool:
        futures = {pool.submit(fetch_one_pr, pr): pr for pr in input_data}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                pr = futures[future]
                results.append({
                    "owner": pr["owner"], "repo": pr["repo"],
                    "number": pr["number"], "error": str(e)
                })

    # Sort results to match input order
    order = {(pr["owner"], pr["repo"], pr["number"]): i for i, pr in enumerate(input_data)}
    results.sort(key=lambda r: order.get((r["owner"], r["repo"], r["number"]), 999))

    json.dump(results, sys.stdout)


if __name__ == "__main__":
    main()
