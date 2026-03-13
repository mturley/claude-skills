# /github-activity

> **Obsolete:** This skill has been superseded by the [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app, which provides the same information in a persistent, auto-refreshing dashboard. The skill still works but will recommend using the dashboard instead when invoked.

Generates a chronological timeline of your GitHub activity over a configurable time period.

## What it shows

- **Day-grouped tables** with timestamps in 12-hour Eastern time
- **Push events** with commit SHA links and commit messages, linked to their associated PR when one exists
- **PR events** (opened, merged, closed, approved, reviewed) with PR titles on every reference
- **Review consolidation** — individual review comments are rolled into their parent review (e.g. "Requested changes (12 comments)")
- **Create/delete events** for branches and repos
- **Summary** with PR counts, approvals, change requests, and commits per repo

## Usage

```
/github-activity        # Last 7 days (default)
/github-activity 14     # Last 14 days
```

## Installation

1. Clone the skills repo and symlink into `~/.claude/skills/`:
   ```bash
   ln -s ~/git/claude-skills/github-activity ~/.claude/skills/github-activity
   ```

2. Ensure `gh` CLI is authenticated:
   ```bash
   gh auth status
   ```

## How it works

Two Python scripts piped together in a single bash call:

1. **fetch-github-activity.py** — Fetches events from the GitHub Events API, then enriches them in parallel using `ThreadPoolExecutor`:
   - PR titles for all referenced PRs
   - Commit messages for push events
   - Branch-to-PR associations (checking upstream repos for cross-fork PRs)

2. **render-github-activity.py** — Converts timestamps, groups by day, renders markdown tables with visual row merging and a summary section.

All Python uses stdlib only (no pip dependencies). Requires only `gh` CLI.
