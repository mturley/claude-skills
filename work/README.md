# /work

Start working on a Jira issue. Identifies the issue, validates the workspace, gathers context from Jira, explores the relevant codebase, and begins implementation.

## Usage

```
/work RHOAIENG-12345
/work https://issues.redhat.com/browse/RHOAIENG-12345
/work                  # auto-detects from branch name or asks
```

## What it does

1. **Identifies the Jira issue** from the argument, current branch name, or conversation history. Asks if it can't determine the issue.
2. **Finds the right repo** to work in. If you're in a non-project directory (like `claude-skills`), it looks for project repos nearby.
3. **Validates the branch** is clean, not on `main`, and up to date with upstream.
4. **Gathers context** from Jira: issue details, acceptance criteria, linked PRs, parent/subtask relationships, and comments.
5. **Explores the codebase** to identify relevant files, components, and existing tests.
6. **Presents a plan** and starts implementing after confirmation.

## Prerequisites

- Atlassian MCP server configured (for Jira access)
- `.context/` symlinked (for `jira-mcp.md` and `people.md`)

## Installation

```bash
ln -s ~/git/claude-skills/work ~/.claude/skills/work
```
