# /activity

Shows a summary of your personal activity on GitHub and Jira for a given day. Useful for keeping a record of what you accomplished.

## Installation

```bash
ln -s ~/git/claude-skills/activity ~/.claude/skills/activity
```

Requires shared directories (if not already linked):
```bash
ln -s ~/git/claude-skills/.context ~/.claude/skills/.context
ln -s ~/git/claude-skills/.shared-scripts ~/.claude/skills/.shared-scripts
```

### Prerequisites

- **GitHub CLI** (`gh`) — authenticated and available in PATH
- **Jira MCP server** — configured with access to the RHOAIENG project
- **Python 3** — stdlib only, no pip dependencies

## Usage

```
/activity              # today's activity
/activity yesterday    # yesterday's activity
/activity March 3      # specific date
/activity 2026-03-05   # ISO date
```

## What It Shows

The report is grouped by activity type:

- **Shipped** — PRs you merged that day
- **Opened** — PRs you opened that day
- **Reviewed** — Reviews and comments on others' PRs (formal reviews, line comments, and general comments)
- **Jira Activity** — Issues where you are assignee or reporter that were updated that day

Each item is cross-referenced: GitHub PRs show linked Jira issues, and Jira issues show linked PRs (via the Git Pull Request custom field).

## How It Works

1. Fetches GitHub activity via the Events API (`/users/{username}/events`), filtered to the target date
2. Searches Jira for issues updated on the target date where the user is assignee or reporter
3. Cross-references GitHub PRs with Jira issues using the Git Pull Request field (`cf[12310220]`)
4. Renders a markdown report grouped by activity type

## Limitations

- **GitHub Events API** only covers the last 90 days and 300 most recent events
- **Jira activity** only captures issues where you are assignee or reporter — issues you only commented on (without being assignee/reporter) are not included

## Helper Scripts

- `fetch-github-activity.py` — Fetches and categorizes GitHub events (PRs opened, merged, reviews/comments submitted). Note: the Events API returns truncated PR objects, so title/author are fetched separately.
- `fetch-pr-details.py` — Fetches PR titles and authors from GitHub API in parallel
- `render-activity-report.py` — Combines GitHub and Jira data, backfills missing PR details, filters self-reviews, cross-references PRs with Jira issues, and renders the final report

(`/activity` is specific to the RHOAIENG Jira project but could be generalized)
