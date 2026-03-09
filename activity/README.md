# /activity

Shows a combined chronological timeline of your Jira and GitHub activity over a configurable time period, merged into a single day-grouped report.

This combines the data from `/jira-activity` and `/github-activity` into one interleaved timeline, so all work activity appears in chronological order regardless of source.

## What it shows

- **Jira changelog actions**: Status transitions, assignments, sprint changes, field updates, PR links, etc. (prefixed with issue type emoji: 🟥 Bug, 🟩 Story, ☑️ Task, ⚡ Epic)
- **Jira comments**: One-line preview of comments posted
- **GitHub push events**: Commit SHA links with messages, linked to associated PRs
- **GitHub PR events**: Opened, merged, closed, approved, reviewed (prefixed with 🐙)
- **GitHub review consolidation**: Review comments rolled into parent review
- **Timestamps**: All converted to Eastern Time (ET) with 12-hour format
- **Row merging**: Consecutive actions on the same issue/PR are visually grouped
- **Combined summary**: Jira stats (changelog actions + comments) and GitHub stats (PRs, commits)

## Usage

```
/activity        # Last 7 days (default)
/activity 14     # Last 14 days
```

## Installation

1. Set up a Jira MCP server (e.g., `@atlassian-dc-mcp/jira` for Jira Datacenter).

2. Ensure `gh` CLI is authenticated:
   ```bash
   gh auth status
   ```

3. Symlink the required directories to `~/.claude/skills/` if you haven't already. See the [root README installation instructions](../README.md#installation).

4. Place the skill at `~/.claude/skills/activity/SKILL.md`.

5. Ensure the `/jira-activity` and `/github-activity` skills are also installed (this skill reuses their fetch scripts).

## Prerequisites

- Jira MCP server configured and accessible
- `gh` CLI authenticated
- Python 3.9+ (stdlib only — no pip dependencies)
- `/jira-activity` and `/github-activity` skills installed

## How it works

Three phases orchestrated by the SKILL.md:

1. **Phase 1 (parallel):** Runs 4 Jira JQL searches with `expand=changelog`, fetches GitHub events via `fetch-github-activity.py`, and reads team config from `people.md`.

2. **Phase 2:** Discovers unique Jira issue keys via `discover-issues.py`, fetches comments for commented issues.

3. **Phase 3:** Runs `render-combined.py` which reads both the Jira search/comment files and the GitHub enriched JSON, merges all events chronologically, and renders a unified markdown timeline.

## Helper Scripts

**`render-combined.py`** — Reads Jira search result files (with `expand=changelog`), Jira comment files, and GitHub enriched JSON. Extracts the user's Jira changelog actions and comments, normalizes GitHub events, merges everything chronologically, groups by day, and renders a unified markdown timeline with emoji source indicators and visual row merging.

Reused from other skills:
- `jira-activity/discover-issues.py` — Jira issue key deduplication
- `github-activity/fetch-github-activity.py` — GitHub event fetching and enrichment
