# /prs

Generates a dashboard of open PRs you're involved with, cross-referenced with RHOAIENG Jira issues. Shows up to four tables: your own open PRs, open PRs you've reviewed or commented on, other open PRs from the current sprint's Jira issues in Review state, and open PRs from Green scrum team members that have no associated Jira issue.

For each PR, the dashboard shows review status, CI status, linked Jira issues (with type, status, sprint, and epic), and highlights where your action is needed.

## Installation

1. Set up a Jira MCP server (e.g., `@atlassian-dc-mcp/jira` for Jira Datacenter).

2. Symlink the `.mcp-usage` directory to `~/.claude/skills/.mcp-usage` if you haven't already. See the [root README installation instructions](../README.md#installation).

3. Place the skill at `~/.claude/skills/prs/SKILL.md`.

## Prerequisites

- GitHub CLI (`gh`) authenticated and available
- Jira MCP server configured and accessible

## Usage

Run `/prs` in any Claude Code session. No arguments needed.

The report is read-only and does not modify any PRs or Jira issues.

## What it shows

- **Review Status** tells you what action is needed:
  - For your PRs: bold **Needs changes** means reviewers left feedback you haven't addressed yet
  - For others' PRs: bold **Needs review** / **Needs re-review** means the author is waiting on you
- **CI**: Passed, Failed, Running, or N/A
- **Jira**: Linked RHOAIENG issues found via the Git Pull Request custom field, with issue type, status, sprint, and epic
- **Table 4** shows team member PRs with no Jira link (requires `.context/people.md` — run `/populate-people` to generate it)
- PRs updated over 1 year ago are excluded (count reported after Table 2)
- Draft PRs and merge conflicts are surfaced in the review status column