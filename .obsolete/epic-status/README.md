# /epic-status

> **Obsolete:** This skill has been superseded by the [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app, which provides the same information in a persistent, auto-refreshing dashboard. The skill still works but will recommend using the dashboard instead when invoked.

Shows all issues in a selected epic, discovered from the current Green sprint. Displays Jira issue details and GitHub PR metadata grouped by workflow status, with sprint information for each issue.

This skill is specific to the RHOAI Dashboard team's Green Scrum, but could be generalized.

## Installation

Requires the [`.context/`](../../.context/) and [`.shared-scripts/`](../../.shared-scripts/) directories to be available as sibling directories. See the [root README installation instructions](../../README.md#installation).

### Prerequisites

- GitHub CLI (`gh`) authenticated and available
- Jira MCP server configured and accessible (e.g., `@atlassian-dc-mcp/jira`)
- Python 3 (stdlib only — no pip dependencies)

## Usage

Run `/epic-status` in any Claude Code session. No arguments needed.

The skill will:
1. Discover epics referenced by issues in the current Green sprint
2. Ask which epic you want to view
3. Fetch all issues in that epic (across all sprints, including sub-tasks)
4. Display a full status report

The report is read-only and does not modify any PRs or Jira issues.

## What It Shows

### Epic Summary

Epic key (linked), summary, total issues, story points (completed/total with percentage), blocked count, and sprints spanned.

### Tables (grouped by status)

Each status group (Review, In Progress, Backlog, Closed/Resolved) gets its own table with:

**Jira columns:** Issue key (linked), type, priority, title, story points, original story points, blocked status, assignee, reporter, last updated, sprint, state

**GitHub columns:** PR link (repo#number), PR last updated, review status (with emoji indicators for action needed)

Issues with multiple linked PRs show continuation rows for additional PRs.

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

- `extract-epic-issues.py` — Parses raw Jira search results and extracts all fields for epic issues. Includes sub-tasks. Collects PR metadata input and sprint names.
- `render-epic-report.py` — Takes fully assembled epic data and renders the markdown report with grouped tables and recommended actions.

### Shared scripts (in `../../.shared-scripts/`)

- `fetch-pr-metadata.py` — Fetches GitHub PR metadata in parallel (shared with `/reviews-status` and `/sprint-status`)
- `jira_utils.py` — Jira field parsing utilities (importable module)
- `format_utils.py` — Markdown formatting utilities (importable module)
