#!/usr/bin/env python3
"""Fetch GitHub activity for a user on a given date via the Events API.

Categorizes events into: PRs opened, PRs merged, reviews submitted.
Commits are deduplicated — only PR-level events are reported.

Input (stdin JSON): {"username": "mturley", "date": "2026-03-06"}
Output (stdout JSON): {
  "prs_opened": [...],
  "prs_merged": [...],
  "reviews": [...],
  "jira_search_paths": [...]
}

Uses only Python stdlib + gh CLI. No pip dependencies.
"""

import json
import subprocess
import sys


def read_stdin():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)
    return json.loads(raw)


def fetch_events(username, target_date):
    """Fetch all events for the user on the target date from GitHub Events API."""
    all_events = []
    page = 1

    while page <= 5:
        try:
            result = subprocess.run(
                ["gh", "api", f"users/{username}/events?per_page=100&page={page}"],
                capture_output=True, text=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            print(f"Warning: gh api timed out on page {page}", file=sys.stderr)
            break

        if result.returncode != 0:
            print(f"Warning: gh api failed on page {page}: {result.stderr.strip()}", file=sys.stderr)
            break

        items = json.loads(result.stdout)
        if not items:
            break

        found_older = False
        for event in items:
            event_date = event.get("created_at", "")[:10]
            if event_date == target_date:
                all_events.append(event)
            elif event_date < target_date:
                found_older = True
                break

        if found_older:
            break
        page += 1

    return all_events


def categorize_events(events, username):
    """Categorize events into PRs opened, merged, and reviews submitted."""
    prs_opened = []
    prs_merged = []
    reviews = []

    seen_opened = set()
    seen_merged = set()
    seen_reviews = set()

    for event in events:
        etype = event.get("type", "")
        payload = event.get("payload", {})
        repo_name = event.get("repo", {}).get("name", "")
        repo_short = repo_name.split("/")[-1] if "/" in repo_name else repo_name

        if etype == "PullRequestEvent":
            action = payload.get("action", "")
            pr = payload.get("pull_request", {})
            pr_key = f"{repo_name}#{pr.get('number', 0)}"

            if action == "opened" and pr_key not in seen_opened:
                seen_opened.add(pr_key)
                prs_opened.append({
                    "repo": repo_short,
                    "repo_full": repo_name,
                    "number": pr.get("number", 0),
                    "title": pr.get("title", ""),
                    "url": pr.get("html_url", ""),
                })

            elif action == "closed" and pr.get("merged") and pr_key not in seen_merged:
                seen_merged.add(pr_key)
                prs_merged.append({
                    "repo": repo_short,
                    "repo_full": repo_name,
                    "number": pr.get("number", 0),
                    "title": pr.get("title", ""),
                    "url": pr.get("html_url", ""),
                })

        elif etype == "PullRequestReviewEvent":
            pr = payload.get("pull_request", {})
            review = payload.get("review", {})
            pr_author = pr.get("user", {}).get("login", "")
            pr_key = f"{repo_name}#{pr.get('number', 0)}"

            # Skip reviews on my own PRs
            if pr_author.lower() == username.lower():
                continue

            if pr_key not in seen_reviews:
                seen_reviews.add(pr_key)
                reviews.append({
                    "repo": repo_short,
                    "repo_full": repo_name,
                    "number": pr.get("number", 0),
                    "title": pr.get("title", ""),
                    "url": pr.get("html_url", ""),
                    "author": pr_author,
                    "state": review.get("state", "commented"),
                })

        elif etype == "PullRequestReviewCommentEvent":
            pr = payload.get("pull_request", {})
            pr_author = pr.get("user", {}).get("login", "")
            pr_key = f"{repo_name}#{pr.get('number', 0)}"

            if pr_author.lower() == username.lower():
                continue

            if pr_key not in seen_reviews:
                seen_reviews.add(pr_key)
                reviews.append({
                    "repo": repo_short,
                    "repo_full": repo_name,
                    "number": pr.get("number", 0),
                    "title": pr.get("title", ""),
                    "url": pr.get("html_url", ""),
                    "author": pr_author,
                    "state": "commented",
                })

        elif etype == "IssueCommentEvent":
            issue = payload.get("issue", {})
            # Only include comments on PRs (issues with pull_request key)
            if "pull_request" not in issue:
                continue
            issue_author = issue.get("user", {}).get("login", "")
            pr_key = f"{repo_name}#{issue.get('number', 0)}"

            if issue_author.lower() == username.lower():
                continue

            if pr_key not in seen_reviews:
                seen_reviews.add(pr_key)
                reviews.append({
                    "repo": repo_short,
                    "repo_full": repo_name,
                    "number": issue.get("number", 0),
                    "title": issue.get("title", ""),
                    "url": issue.get("html_url", ""),
                    "author": issue_author,
                    "state": "commented",
                })

    return prs_opened, prs_merged, reviews


def build_jira_search_paths(prs_opened, prs_merged, reviews):
    """Build partial paths for Jira cross-reference search."""
    seen = set()
    paths = []
    for pr in prs_opened + prs_merged + reviews:
        path = f"{pr['repo_full']}/pull/{pr['number']}"
        if path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def main():
    data = read_stdin()
    username = data["username"]
    target_date = data["date"]

    events = fetch_events(username, target_date)
    prs_opened, prs_merged, reviews = categorize_events(events, username)
    jira_search_paths = build_jira_search_paths(prs_opened, prs_merged, reviews)

    result = {
        "prs_opened": prs_opened,
        "prs_merged": prs_merged,
        "reviews": reviews,
        "jira_search_paths": jira_search_paths,
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
