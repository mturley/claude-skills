#!/usr/bin/env python3
"""Fetch GitHub activity events and enrich with PR titles, commit messages, and branch-PR mappings.

Reads JSON from stdin: {"username": "...", "days": 7}
Fetches events from the GitHub Events API, then enriches in parallel:
  - PR titles for all referenced PRs
  - First line of commit messages for all push events
  - Branch-to-PR associations for non-default-branch pushes

Outputs enriched JSON to stdout for piping to render-github-activity.py.

Uses only Python stdlib. Requires `gh` CLI to be authenticated.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone


DEFAULT_BRANCHES = {"main", "master", "develop", "dev"}


def run_gh(args, timeout=30):
    """Run a gh command and return stdout."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True, text=True, timeout=timeout
    )
    return result.stdout, result.returncode


def fetch_events(username, cutoff_iso):
    """Fetch all events from the GitHub Events API, filtered by cutoff date."""
    # --paginate with --jq '.[]' flattens paginated arrays into one JSON object per line
    stdout, rc = run_gh([
        "api", f"users/{username}/events",
        "--paginate",
        "--jq", ".[]",
    ], timeout=120)

    if rc != 0 or not stdout.strip():
        return []

    # Parse newline-delimited JSON objects
    all_events = []
    decoder = json.JSONDecoder()
    raw = stdout.strip()
    pos = 0
    while pos < len(raw):
        # Skip whitespace
        while pos < len(raw) and raw[pos] in " \t\n\r":
            pos += 1
        if pos >= len(raw):
            break
        try:
            obj, end = decoder.raw_decode(raw, pos)
            all_events.append(obj)
            pos = end
        except json.JSONDecodeError:
            break

    # Filter by cutoff date
    filtered = []
    for event in all_events:
        created = event.get("created_at", "")
        if created >= cutoff_iso:
            filtered.append(event)

    return filtered


def parse_repo_name(full_name):
    """Split 'owner/repo' into (owner, repo)."""
    parts = full_name.split("/", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (full_name, "")


def extract_pr_info(event):
    """Extract PR owner/repo/number from an event's payload, if present."""
    payload = event.get("payload", {})
    pr = payload.get("pull_request") or payload.get("issue", {})
    if not pr:
        return None
    number = pr.get("number")
    if not number:
        return None
    # Get the base repo (upstream) for the PR
    base = pr.get("base", {})
    base_repo = base.get("repo", {})
    if base_repo:
        repo_full = base_repo.get("full_name", "")
        if repo_full:
            owner, repo = parse_repo_name(repo_full)
            return (owner, repo, number)
    # Fallback to event repo
    repo_full = event.get("repo", {}).get("name", "")
    owner, repo = parse_repo_name(repo_full)
    return (owner, repo, number)


def process_events(events, username):
    """Process raw events into normalized entries and collect enrichment needs."""
    IGNORED_TYPES = {"WatchEvent", "ForkEvent", "MemberEvent", "PublicEvent", "GollumEvent"}

    entries = []
    pr_titles_needed = {}  # (owner, repo, number) -> None
    commits_needed = {}    # (owner, repo, sha) -> None
    branch_pr_needed = {}  # (fork_owner, repo, branch) -> upstream_owner or None

    # Track upstream repos for branches (from PR events)
    # First pass: collect upstream context from PR events
    # The Events API strips head.repo and base.repo data, but we have:
    # - event.repo.name: the upstream repo (e.g. "kubeflow/model-registry")
    # - head.ref: the branch name
    # We map branch names to upstream repos they're associated with.
    branch_to_upstreams = {}  # branch_name -> set of upstream_full_names
    all_upstream_repos = set()  # all unique upstream repos seen in PR events
    for event in events:
        if event["type"] in ("PullRequestEvent", "PullRequestReviewEvent",
                             "PullRequestReviewCommentEvent"):
            payload = event.get("payload", {})
            pr = payload.get("pull_request", {})
            if not pr:
                continue
            head = pr.get("head", {})
            head_ref = head.get("ref", "")
            event_repo = event.get("repo", {}).get("name", "")
            if head_ref and event_repo:
                event_owner, _ = parse_repo_name(event_repo)
                # If the event repo is different from the user's fork, it's upstream
                if event_owner != username:
                    if head_ref not in branch_to_upstreams:
                        branch_to_upstreams[head_ref] = set()
                    branch_to_upstreams[head_ref].add(event_repo)
                    all_upstream_repos.add(event_repo)

    # Second pass: process events
    for event in events:
        event_type = event.get("type", "")
        if event_type in IGNORED_TYPES:
            continue

        created = event.get("created_at", "")
        repo_full = event.get("repo", {}).get("name", "")
        owner, repo = parse_repo_name(repo_full)
        payload = event.get("payload", {})

        if event_type == "PushEvent":
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "")
            head_sha = payload.get("head", "")
            commits = payload.get("commits", [])

            # Determine if this is a default branch
            is_default = branch in DEFAULT_BRANCHES

            # Collect branch-to-PR lookup if non-default
            if not is_default:
                key = (owner, repo, branch)
                if key not in branch_pr_needed:
                    # Try matching by branch name to find the upstream repo
                    upstream = None
                    if branch in branch_to_upstreams:
                        upstreams = branch_to_upstreams[branch]
                        upstream = next(iter(upstreams)) if len(upstreams) == 1 else None
                    branch_pr_needed[key] = upstream

            # Create one entry per commit
            if commits:
                for commit in commits:
                    sha = commit.get("sha", "")
                    msg = commit.get("message", "")
                    first_line = msg.split("\n")[0] if msg else ""
                    entries.append({
                        "timestamp": created,
                        "type": "push",
                        "owner": owner,
                        "repo": repo,
                        "branch": branch,
                        "is_default_branch": is_default,
                        "commit_sha": sha,
                        "commit_message": first_line,
                        "commit_url": f"https://github.com/{repo_full}/commit/{sha}",
                    })
            elif head_sha:
                # No inline commits (common for large pushes), need to fetch
                commits_needed[(owner, repo, head_sha)] = None
                entries.append({
                    "timestamp": created,
                    "type": "push",
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "is_default_branch": is_default,
                    "commit_sha": head_sha,
                    "commit_message": None,  # Will be enriched
                    "commit_url": f"https://github.com/{repo_full}/commit/{head_sha}",
                })

        elif event_type == "PullRequestEvent":
            action = payload.get("action", "")
            pr = payload.get("pull_request", {})
            merged = pr.get("merged", False)
            pr_info = extract_pr_info(event)

            if action == "closed" and merged:
                action = "merged"

            if pr_info:
                pr_owner, pr_repo, pr_number = pr_info
                pr_titles_needed[(pr_owner, pr_repo, pr_number)] = None
                entries.append({
                    "timestamp": created,
                    "type": "pr",
                    "owner": owner,
                    "repo": repo,
                    "action": action,
                    "pr_owner": pr_owner,
                    "pr_repo": pr_repo,
                    "pr_number": pr_number,
                    "pr_url": f"https://github.com/{pr_owner}/{pr_repo}/pull/{pr_number}",
                })

        elif event_type == "PullRequestReviewEvent":
            review = payload.get("review", {})
            state = review.get("state", "")
            pr_info = extract_pr_info(event)

            if pr_info:
                pr_owner, pr_repo, pr_number = pr_info
                pr_titles_needed[(pr_owner, pr_repo, pr_number)] = None
                entries.append({
                    "timestamp": created,
                    "type": "review",
                    "owner": owner,
                    "repo": repo,
                    "action": state,  # approved, changes_requested, commented
                    "pr_owner": pr_owner,
                    "pr_repo": pr_repo,
                    "pr_number": pr_number,
                    "pr_url": f"https://github.com/{pr_owner}/{pr_repo}/pull/{pr_number}",
                })

        elif event_type == "PullRequestReviewCommentEvent":
            pr_info = extract_pr_info(event)
            if pr_info:
                pr_owner, pr_repo, pr_number = pr_info
                pr_titles_needed[(pr_owner, pr_repo, pr_number)] = None
                entries.append({
                    "timestamp": created,
                    "type": "review_comment",
                    "owner": owner,
                    "repo": repo,
                    "pr_owner": pr_owner,
                    "pr_repo": pr_repo,
                    "pr_number": pr_number,
                    "pr_url": f"https://github.com/{pr_owner}/{pr_repo}/pull/{pr_number}",
                })

        elif event_type == "IssueCommentEvent":
            action = payload.get("action", "")
            issue = payload.get("issue", {})
            # Check if this is a PR comment (issues API includes PRs)
            is_pr = "pull_request" in issue
            number = issue.get("number")

            if number:
                if is_pr:
                    pr_info = extract_pr_info(event)
                    if pr_info:
                        pr_owner, pr_repo, pr_number = pr_info
                    else:
                        pr_owner, pr_repo, pr_number = owner, repo, number
                    pr_titles_needed[(pr_owner, pr_repo, pr_number)] = None
                    entries.append({
                        "timestamp": created,
                        "type": "issue_comment",
                        "owner": owner,
                        "repo": repo,
                        "pr_owner": pr_owner,
                        "pr_repo": pr_repo,
                        "pr_number": pr_number,
                        "pr_url": f"https://github.com/{pr_owner}/{pr_repo}/pull/{pr_number}",
                    })
                else:
                    entries.append({
                        "timestamp": created,
                        "type": "issue_comment",
                        "owner": owner,
                        "repo": repo,
                        "issue_number": number,
                        "issue_title": issue.get("title", ""),
                        "issue_url": issue.get("html_url", ""),
                    })

        elif event_type == "CreateEvent":
            ref_type = payload.get("ref_type", "")
            ref = payload.get("ref", "")
            entries.append({
                "timestamp": created,
                "type": "create",
                "owner": owner,
                "repo": repo,
                "ref_type": ref_type,
                "ref": ref or "",
            })

        elif event_type == "DeleteEvent":
            ref_type = payload.get("ref_type", "")
            ref = payload.get("ref", "")
            entries.append({
                "timestamp": created,
                "type": "delete",
                "owner": owner,
                "repo": repo,
                "ref_type": ref_type,
                "ref": ref or "",
            })

        elif event_type == "ReleaseEvent":
            action = payload.get("action", "")
            release = payload.get("release", {})
            tag = release.get("tag_name", "")
            entries.append({
                "timestamp": created,
                "type": "release",
                "owner": owner,
                "repo": repo,
                "action": action,
                "tag": tag,
            })

    return entries, pr_titles_needed, commits_needed, branch_pr_needed, all_upstream_repos


def fetch_pr_title(owner, repo, number):
    """Fetch a PR title from GitHub."""
    stdout, rc = run_gh([
        "api", f"repos/{owner}/{repo}/pulls/{number}",
        "--jq", ".title",
    ])
    if rc == 0 and stdout.strip():
        return stdout.strip()
    return None


def fetch_commit_message(owner, repo, sha):
    """Fetch the first line of a commit message."""
    stdout, rc = run_gh([
        "api", f"repos/{owner}/{repo}/commits/{sha}",
        "--jq", ".commit.message",
    ])
    if rc == 0 and stdout.strip():
        return stdout.strip().split("\n")[0]
    return None


def fetch_branch_pr(fork_owner, repo_name, branch, upstream_full, all_upstreams=None):
    """Look up the PR associated with a branch.

    Try upstream first, then fork, then all known upstream repos.
    """
    targets = []
    if upstream_full:
        targets.append(upstream_full)
    targets.append(f"{fork_owner}/{repo_name}")
    # Also try all known upstream repos as a fallback
    if all_upstreams:
        for up in all_upstreams:
            if up not in targets:
                targets.append(up)

    for target in targets:
        stdout, rc = run_gh([
            "api", f"repos/{target}/pulls?head={fork_owner}:{branch}&state=all",
            "--jq", ".[0] | {number, title}",
        ])
        if rc == 0 and stdout.strip() and stdout.strip() != "null":
            try:
                data = json.loads(stdout)
                if data and data.get("number"):
                    t_owner, t_repo = parse_repo_name(target)
                    return {
                        "pr_owner": t_owner,
                        "pr_repo": t_repo,
                        "pr_number": data["number"],
                        "pr_title": data.get("title", ""),
                        "pr_url": f"https://github.com/{target}/pull/{data['number']}",
                    }
            except json.JSONDecodeError:
                continue
    return None


def enrich_parallel(pr_titles_needed, commits_needed, branch_pr_needed, all_upstreams=None):
    """Fetch all enrichment data in parallel."""
    pr_titles = {}       # (owner, repo, number) -> title
    commit_messages = {} # (owner, repo, sha) -> first line
    branch_prs = {}      # (fork_owner, repo, branch) -> {pr_owner, pr_repo, pr_number, pr_title, pr_url}

    total_calls = len(pr_titles_needed) + len(commits_needed) + len(branch_pr_needed)
    if total_calls == 0:
        return pr_titles, commit_messages, branch_prs

    workers = min(20, total_calls)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}

        # Submit PR title fetches
        for (owner, repo, number) in pr_titles_needed:
            future = pool.submit(fetch_pr_title, owner, repo, number)
            futures[future] = ("pr_title", owner, repo, number)

        # Submit commit message fetches
        for (owner, repo, sha) in commits_needed:
            future = pool.submit(fetch_commit_message, owner, repo, sha)
            futures[future] = ("commit", owner, repo, sha)

        # Submit branch-to-PR lookups
        for (fork_owner, repo_name, branch), upstream in branch_pr_needed.items():
            future = pool.submit(fetch_branch_pr, fork_owner, repo_name, branch, upstream, all_upstreams)
            futures[future] = ("branch_pr", fork_owner, repo_name, branch)

        for future in as_completed(futures):
            key = futures[future]
            try:
                result = future.result()
            except Exception:
                continue

            if key[0] == "pr_title" and result:
                _, owner, repo, number = key
                pr_titles[(owner, repo, number)] = result
            elif key[0] == "commit" and result:
                _, owner, repo, sha = key
                commit_messages[(owner, repo, sha)] = result
            elif key[0] == "branch_pr" and result:
                _, fork_owner, repo_name, branch = key
                branch_prs[(fork_owner, repo_name, branch)] = result
                # Also store the PR title so we don't need a separate lookup
                pr_info = result
                title_key = (pr_info["pr_owner"], pr_info["pr_repo"], pr_info["pr_number"])
                if title_key not in pr_titles:
                    pr_titles[title_key] = pr_info["pr_title"]

    return pr_titles, commit_messages, branch_prs


def apply_enrichment(entries, pr_titles, commit_messages, branch_prs):
    """Apply enrichment data back to entries."""
    for entry in entries:
        # Enrich PR titles
        if "pr_owner" in entry and "pr_number" in entry:
            title_key = (entry["pr_owner"], entry["pr_repo"], entry["pr_number"])
            if title_key in pr_titles and "pr_title" not in entry:
                entry["pr_title"] = pr_titles[title_key]

        # Enrich commit messages
        if entry["type"] == "push" and entry.get("commit_message") is None:
            msg_key = (entry["owner"], entry["repo"], entry["commit_sha"])
            if msg_key in commit_messages:
                entry["commit_message"] = commit_messages[msg_key]

        # Enrich push events with branch-to-PR mapping
        if entry["type"] == "push" and not entry.get("is_default_branch"):
            branch_key = (entry["owner"], entry["repo"], entry["branch"])
            if branch_key in branch_prs:
                pr_info = branch_prs[branch_key]
                entry["pr_owner"] = pr_info["pr_owner"]
                entry["pr_repo"] = pr_info["pr_repo"]
                entry["pr_number"] = pr_info["pr_number"]
                entry["pr_title"] = pr_info["pr_title"]
                entry["pr_url"] = pr_info["pr_url"]


def consolidate_reviews(entries):
    """Consolidate review comment events into their parent review events.

    Strategy: For each review submission event, absorb all review_comment
    events on the same PR that occur before it (up to the previous review
    event on that PR). Also deduplicate duplicate review events.
    """
    # Sort chronologically
    entries.sort(key=lambda e: e["timestamp"])

    # Deduplicate review events: same PR + same action + same timestamp
    seen_reviews = set()
    deduped = []
    for entry in entries:
        if entry["type"] == "review":
            key = (entry.get("pr_owner"), entry.get("pr_repo"),
                   entry.get("pr_number"), entry.get("action"), entry["timestamp"])
            if key in seen_reviews:
                continue
            seen_reviews.add(key)
        deduped.append(entry)
    entries = deduped

    # For each review event, absorb preceding review_comment events on the same PR
    consumed = set()
    for i, entry in enumerate(entries):
        if entry["type"] != "review":
            continue

        pr_key = (entry.get("pr_owner"), entry.get("pr_repo"), entry.get("pr_number"))
        comment_count = 0
        earliest_time = entry["timestamp"]

        # Walk backward from this review event
        for j in range(i - 1, -1, -1):
            prev = entries[j]
            if j in consumed:
                continue
            prev_pr_key = (prev.get("pr_owner"), prev.get("pr_repo"), prev.get("pr_number"))

            if prev_pr_key != pr_key:
                continue

            # Stop at a previous review event on the same PR
            if prev["type"] == "review":
                break

            if prev["type"] == "review_comment":
                consumed.add(j)
                comment_count += 1
                if prev["timestamp"] < earliest_time:
                    earliest_time = prev["timestamp"]

        if comment_count > 0:
            entry["review_comment_count"] = comment_count
            entry["review_time_start"] = earliest_time

    # Remove consumed entries
    entries = [e for i, e in enumerate(entries) if i not in consumed]
    return entries


def deduplicate_commits(entries):
    """Remove duplicate push entries with the same repo and SHA."""
    seen = set()
    deduped = []
    for entry in entries:
        if entry["type"] == "push":
            key = (entry["owner"], entry["repo"], entry["commit_sha"])
            if key in seen:
                continue
            seen.add(key)
        deduped.append(entry)
    return deduped


def build_summary(entries):
    """Build summary statistics from enriched entries."""
    prs_opened = []
    prs_merged = []
    prs_closed = []
    prs_approved = []
    reviews_requested_changes = []
    repos_with_commits = {}

    seen_prs = {}  # (pr_owner, pr_repo, pr_number) -> {title, url}

    for entry in entries:
        if entry["type"] == "pr":
            pr_key = (entry.get("pr_owner"), entry.get("pr_repo"), entry.get("pr_number"))
            pr_ref = {
                "repo": f"{entry.get('pr_owner')}/{entry.get('pr_repo')}",
                "number": entry.get("pr_number"),
                "title": entry.get("pr_title", ""),
                "url": entry.get("pr_url", ""),
            }
            action = entry.get("action", "")
            if action == "opened":
                prs_opened.append(pr_ref)
            elif action == "merged":
                prs_merged.append(pr_ref)
            elif action == "closed":
                prs_closed.append(pr_ref)

        elif entry["type"] == "review":
            action = entry.get("action", "")
            pr_ref = {
                "repo": f"{entry.get('pr_owner')}/{entry.get('pr_repo')}",
                "number": entry.get("pr_number"),
                "title": entry.get("pr_title", ""),
                "url": entry.get("pr_url", ""),
            }
            if action == "approved":
                prs_approved.append(pr_ref)
            elif action == "changes_requested":
                pr_ref["comment_count"] = entry.get("review_comment_count", 0)
                reviews_requested_changes.append(pr_ref)

        elif entry["type"] == "push":
            repo_full = f"{entry['owner']}/{entry['repo']}"
            repos_with_commits[repo_full] = repos_with_commits.get(repo_full, 0) + 1

    return {
        "prs_opened": prs_opened,
        "prs_merged": prs_merged,
        "prs_closed": prs_closed,
        "prs_approved": prs_approved,
        "reviews_requested_changes": reviews_requested_changes,
        "repos_with_commits": repos_with_commits,
    }


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(raw)
    username = data.get("username", "")
    days = data.get("days", 7)

    if not username:
        print("Error: 'username' is required.", file=sys.stderr)
        sys.exit(1)

    # Calculate cutoff
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    cutoff_date = cutoff.strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")

    # Fetch events
    events = fetch_events(username, cutoff_iso)

    # Process into entries and collect enrichment needs
    entries, pr_titles_needed, commits_needed, branch_pr_needed, all_upstreams = process_events(events, username)

    # Deduplicate commits before enrichment
    entries = deduplicate_commits(entries)

    # Remove commit enrichment requests for commits that already have messages
    for entry in entries:
        if entry["type"] == "push" and entry.get("commit_message"):
            key = (entry["owner"], entry["repo"], entry["commit_sha"])
            commits_needed.pop(key, None)

    # Remove PR title requests for PRs discovered via branch lookups
    # (will be handled during enrichment)

    # Enrich in parallel
    pr_titles, commit_messages, branch_prs = enrich_parallel(
        pr_titles_needed, commits_needed, branch_pr_needed, all_upstreams
    )

    # Apply enrichment
    apply_enrichment(entries, pr_titles, commit_messages, branch_prs)

    # Consolidate review comments
    entries = consolidate_reviews(entries)

    # Build summary
    summary = build_summary(entries)

    output = {
        "username": username,
        "cutoff": cutoff_date,
        "today": today,
        "events": entries,
        "summary": summary,
    }

    json.dump(output, sys.stdout)


if __name__ == "__main__":
    main()
