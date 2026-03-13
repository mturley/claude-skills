# /jira-activity

> **Obsolete:** This skill has been superseded by the [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app, which provides the same information in a persistent, auto-refreshing dashboard. The skill still works but will recommend using the dashboard instead when invoked.

Shows a chronological timeline of your Jira activity over a configurable time period. Extracts changelog actions (status transitions, assignments, field changes, PR links) and comments from all issues you've touched, rendered with issue type/priority emojis, hyperlinked Jira issues and PRs, and times converted to Eastern Time.

This skill is specific to the RHOAI Dashboard team's Green Scrum, but could be generalized.

## Installation

1. Set up a Jira MCP server (e.g., `@atlassian-dc-mcp/jira` for Jira Datacenter).

2. Symlink the `.context` directory to `~/.claude/skills/.context` if you haven't already. See the [root README installation instructions](../README.md#installation).

3. Place the skill at `~/.claude/skills/jira-activity/SKILL.md`.

## Prerequisites

- Jira MCP server configured and accessible
- Python 3.9+ (stdlib only — no pip dependencies; uses `zoneinfo` for timezone conversion)

## Usage

Run `/jira-activity` in any Claude Code session. Defaults to the last 7 days.

Optional argument: `/jira-activity 14` — look back 14 days instead of 7.

The report is read-only and does not modify any Jira issues.

## Helper Scripts

All scripts use Python 3 stdlib only (no pip dependencies). Both accept file paths as CLI arguments, reading persisted Jira MCP tool-result files directly from disk.

`discover-issues.py` reads 4 persisted search result files (`--assignee`, `--watcher`, `--reporter`, `--commenter`) and deduplicates issue keys. Outputs `{issue_keys, commented_keys, total}` for driving the comment fetch phase.

`render-activity.py` reads search result files (`--search-files`, containing issues with `expand=changelog`) and comment files (`--comment-files` as `ISSUE_KEY=/path/to/file.json`). Extracts the specified user's changelog actions and comments, filters by date range, converts timestamps to the target timezone, groups by day, merges consecutive same-issue rows, and renders the full markdown timeline with emoji indicators.

## What it shows

- **Changelog actions**: Status transitions, assignments, sprint changes, field updates, PR links, blocked status, epic child additions, duplicate links, etc.
- **Comments**: One-line preview of comments the user posted
- **Type & Priority**: Emoji indicators matching the `/reviews-status` conventions (🟥 Bug, 🟩 Story, ☑️ Task, ⚡ Epic; ⛔ Blocker, 🔺 Critical, 🔶 Major, 🔵 Normal)
- **Timestamps**: Converted from Jira UTC to Eastern Time (ET) with automatic DST handling
- **Merged rows**: When consecutive actions are on the same issue, the Issue/Type/Priority cells are left blank for visual grouping
- Description changes are summarized as "Updated description" to avoid verbose diffs
