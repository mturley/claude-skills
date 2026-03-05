# /reviews-status

Shows the review status of open PRs across your work, your team's sprint, and your scrum members, cross-referenced with RHOAIENG Jira issues. Highlights where your action is needed with emoji indicators and links to Jira issues with type, status, sprint, and epic.

This skill is specific to the RHOAI Dashboard team's Green Scrum, but could be generalized.

## Installation

1. Set up a Jira MCP server (e.g., `@atlassian-dc-mcp/jira` for Jira Datacenter).

2. Symlink the `.context` directory to `~/.claude/skills/.context` if you haven't already. See the [root README installation instructions](../README.md#installation).

3. Place the skill at `~/.claude/skills/reviews-status/SKILL.md`.

## Prerequisites

- GitHub CLI (`gh`) authenticated and available
- Jira MCP server configured and accessible
- Python 3 (stdlib only — no pip dependencies)

## Usage

Run `/reviews-status` in any Claude Code session. No arguments needed.

The report is read-only and does not modify any PRs or Jira issues.

## Helper Scripts

All scripts use stdin/stdout JSON, Python 3 stdlib only (no pip dependencies).

`fetch-pr-metadata.py` fetches GitHub PR metadata in parallel using `concurrent.futures.ThreadPoolExecutor`. Pipes in `[{owner, repo, number}]`, gets back labels, draft status, mergeable state, review count, timestamps, CI status, and pre-computed review status strings. Replaces serial `gh api` calls with concurrent ones.

`extract-jira-fields.py` parses raw Jira search responses into compact JSON with only the fields needed by the skill. Auto-detects three input formats (raw response, tool-result wrapper, direct issues array). Supports `--filter-sprint Green` to filter by sprint name.

`assign-tables.py` handles PR deduplication, age filtering, and table assignment between phases. Two subcommands: `deduplicate` (after Phase 1) splits PRs into Table 1/2 and generates Jira search paths; `assign` (after Phase 2) processes sprint review issues and team PRs into Table 3/4 candidates.

`render-report.py` takes fully assembled table data and renders the complete markdown report. Handles sorting by Jira priority, title truncation, date formatting, multi-Jira rows, and auto-generates the Recommended Actions section.

## What it shows

- **Review Status** tells you what action is needed (computed by `fetch-pr-metadata.py`):
  - For your PRs: bold **Has new comments** means reviewers left feedback you haven't addressed yet
  - For others' PRs: bold **Needs review** / **Needs re-review** means the author is waiting on you
- **Jira**: Linked RHOAIENG issues found via the Git Pull Request custom field, with issue type, status, sprint, and epic
- **Table 4** shows team member PRs with no Jira link (requires `.context/people.md` — run `/populate-people` to generate it)
- PRs updated over 1 year ago are excluded (count reported after Table 2)
- Draft PRs and merge conflicts are surfaced in the review status column