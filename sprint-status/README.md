# /sprint-status

Shows the current Green sprint status with all tickets grouped by workflow status (Review, In Progress, Backlog, Closed/Resolved). Each section includes a table with Jira issue details and linked GitHub PR metadata.

This skill is specific to the RHOAI Dashboard team's Green Scrum, but could be generalized.

## Installation

Requires the [`.context/`](../.context/) and [`.shared-scripts/`](../.shared-scripts/) directories to be available as sibling directories. See the [root README installation instructions](../README.md#installation).

### Prerequisites

- GitHub CLI (`gh`) authenticated and available
- Jira MCP server configured and accessible (e.g., `@atlassian-dc-mcp/jira`)
- Python 3 (stdlib only — no pip dependencies)

## Usage

Run `/sprint-status` in any Claude Code session. No arguments needed.

The report is read-only and does not modify any PRs or Jira issues.

## What It Shows

### Tables (grouped by status)

Each status group (Review, In Progress, Backlog, Closed/Resolved) gets its own table with:

**Jira columns:** Issue key (linked), type, priority, title, story points, original story points, blocked status, assignee, reporter, last updated, epic (linked with short name)

**GitHub columns:** PR link (repo#number), PR last updated, review status (with emoji indicators for action needed)

Issues with multiple linked PRs show continuation rows for additional PRs.

### Summary

Sprint name, goal, total issues, total story points, and blocked count.

### Recommended Actions

Prioritized list sorted by Jira priority, including:
1. Your PRs in Review needing attention (comments, CI failures)
2. Teammate PRs needing review from you
3. Blocked issues needing unblocking
4. Approved PRs ready to merge
5. High-priority backlog items
6. Issues in progress with no linked PR

Each PR action includes a `/pr-worktree` code block for easy review.

## Helper Scripts

All scripts use stdin/stdout JSON, Python 3 stdlib only.

- `extract-sprint-issues.py` — Parses raw Jira search results and extracts all sprint-relevant fields. Supports `--filter-sprint` to filter by sprint name. Collects PR metadata input and epic keys for Phase 2.
- `render-sprint-report.py` — Takes fully assembled sprint data and renders the markdown report with grouped tables and recommended actions.

### Shared scripts (in `../.shared-scripts/`)

- `fetch-pr-metadata.py` — Fetches GitHub PR metadata in parallel (shared with `/reviews-status`)
- `jira_utils.py` — Jira field parsing utilities (importable module)
- `format_utils.py` — Markdown formatting utilities (importable module)
