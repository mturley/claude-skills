#!/usr/bin/env python3
"""Fetch GitHub PR metadata in parallel.

Reads a JSON array of {owner, repo, number} objects from stdin.
Outputs a JSON array with metadata for each PR:
  state, draft, labels, mergeable_state, review_count, last_review_at,
  last_commit_at, ci_status, review_decision

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


def fetch_pr_data(owner, repo, number):
    """Fetch all PR metadata in a single gh pr view --json call."""
    fields = ",".join([
        "isDraft", "labels", "mergeStateStatus", "reviewDecision",
        "reviews", "statusCheckRollup", "commits", "state",
    ])
    stdout, _, rc = run_gh([
        "pr", "view", str(number), "--repo", f"{owner}/{repo}",
        "--json", fields,
    ])
    if rc != 0 or not stdout.strip():
        return None
    data = json.loads(stdout)

    # Extract labels
    labels = [label["name"] for label in data.get("labels", [])]

    # Extract review info
    reviews = data.get("reviews", [])
    review_count = len(reviews)
    sorted_reviews = sorted(reviews, key=lambda r: r.get("submittedAt", ""))
    last_review_at = sorted_reviews[-1]["submittedAt"] if sorted_reviews else None

    # Extract last commit date
    commits = data.get("commits", [])
    last_commit_at = commits[-1]["committedDate"] if commits else None

    # Compute CI status from statusCheckRollup
    checks = data.get("statusCheckRollup") or []
    ci_status = "N/A"
    if checks:
        has_fail = any(c.get("conclusion") == "FAILURE" for c in checks)
        has_pending = any(c.get("status") == "IN_PROGRESS" for c in checks)
        has_pass = any(c.get("conclusion") == "SUCCESS" for c in checks)
        if has_fail:
            ci_status = "Failed"
        elif has_pending:
            ci_status = "Running"
        elif has_pass:
            ci_status = "Passed"

    # Map mergeStateStatus to mergeable_state for backward compatibility
    merge_state = data.get("mergeStateStatus", "UNKNOWN")
    mergeable_state = "dirty" if merge_state == "DIRTY" else merge_state.lower()

    return {
        "state": data.get("state", "unknown").lower(),
        "draft": data.get("isDraft", False),
        "labels": labels,
        "mergeable_state": mergeable_state,
        "review_count": review_count,
        "last_review_at": last_review_at,
        "last_commit_at": last_commit_at,
        "ci_status": ci_status,
        "review_decision": data.get("reviewDecision", ""),
    }


def compute_review_status(pr_data, is_mine):
    """Compute the formatted review status string for a PR.

    Args:
        pr_data: dict with draft, labels, review_count, last_review_at,
                 last_commit_at, mergeable_state, ci_status, review_decision
        is_mine: True for my PRs, False for others' PRs

    Returns:
        Formatted markdown string ready for table cell.
    """
    draft = pr_data.get("draft", False)
    labels = pr_data.get("labels", [])
    review_count = pr_data.get("review_count", 0)
    last_review_at = pr_data.get("last_review_at")
    last_commit_at = pr_data.get("last_commit_at")
    mergeable_state = pr_data.get("mergeable_state", "")
    ci_status = pr_data.get("ci_status", "N/A")
    review_decision = pr_data.get("review_decision", "")

    has_lgtm = "lgtm" in labels
    has_approved = "approved" in labels
    changes_requested = review_decision == "CHANGES_REQUESTED"

    # Evaluate conditions top-to-bottom, stop at first match
    if draft:
        status, bold, emoji = "Draft", False, ""
    elif has_lgtm and has_approved:
        status, bold, emoji = "Approved", False, ""
    elif has_lgtm and not has_approved:
        if is_mine:
            status, bold, emoji = "Waiting for approval", False, ""
        else:
            status, bold, emoji = "Needs approval", True, "\U0001f7e2"
    elif changes_requested and last_review_at and last_commit_at and last_review_at > last_commit_at:
        if is_mine:
            status, bold, emoji = "Changes requested", True, "\U0001f534"
        else:
            status, bold, emoji = "Waiting for changes", False, ""
    elif review_count > 0 and last_review_at and last_commit_at and last_commit_at > last_review_at:
        if is_mine:
            status, bold, emoji = "Waiting for re-review", False, ""
        else:
            if not has_lgtm:
                status, bold, emoji = "Needs re-review", True, "\U0001f535"
            else:
                status, bold, emoji = "Waiting for re-review", False, ""
    elif review_count > 0 and last_review_at and last_commit_at and last_review_at > last_commit_at and not has_lgtm:
        if is_mine:
            status, bold, emoji = "Has new comments", True, "\U0001f7e0"
        else:
            status, bold, emoji = "Has comments", False, ""
    elif review_count == 0:
        if is_mine:
            status, bold, emoji = "Waiting for review", False, ""
        else:
            status, bold, emoji = "Needs review", True, "\U0001f7e1"
    else:
        status, bold, emoji = "Unknown", False, ""

    # Format with bold and emoji
    formatted = f"**{status}**" if bold else status
    if emoji:
        formatted = f"{emoji} {formatted}"

    # Append suffixes
    if mergeable_state == "dirty":
        formatted += " **(conflicts)**"
    if ci_status == "Failed":
        formatted += " (CI failed)"

    return formatted


def fetch_one_pr(pr):
    """Fetch all metadata for a single PR."""
    owner = pr["owner"]
    repo = pr["repo"]
    number = pr["number"]

    data = fetch_pr_data(owner, repo, number)
    if data is None:
        return {
            "owner": owner, "repo": repo, "number": number,
            "error": "Failed to fetch PR info"
        }

    result = {
        "owner": owner,
        "repo": repo,
        "number": number,
        **data,
    }

    # Compute review status for both perspectives
    result["review_status_mine"] = compute_review_status(result, is_mine=True)
    result["review_status_others"] = compute_review_status(result, is_mine=False)

    return result


def main():
    input_data = json.load(sys.stdin)
    if not input_data:
        json.dump([], sys.stdout)
        return

    results = []
    with ThreadPoolExecutor(max_workers=min(30, len(input_data))) as pool:
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
