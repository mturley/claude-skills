# /populate-people

Generates or updates `.context/people.md` with RHOAI Dashboard team member information by cross-referencing Confluence, Jira, and GitHub.

## Installation

Place at `~/.claude/skills/populate-people/` (or symlink from this repo).

Requires the shared MCP documentation directory:
```bash
ln -s ~/git/claude-skills/.mcp-usage ~/.claude/skills/.mcp-usage
```

## Prerequisites

- **Confluence MCP** configured with access to `spaces.redhat.com`
- **Jira MCP** configured with access to `issues.redhat.com`
- **GitHub CLI** (`gh`) authenticated

## Usage

```
/populate-people
```

On first run, the skill generates `.context/people.md` from scratch by:
1. Fetching the team structure from the [Exploring Team Configuration](https://spaces.redhat.com/spaces/RHODS/pages/479331996/Exploring+Team+Configuration) Confluence page
2. Resolving Confluence user keys to real names via the REST API
3. Looking up Jira usernames and email addresses
4. Finding GitHub usernames from repo contributor lists and commit history

On subsequent runs, it compares the existing file against Confluence and reports any changes (new members, departures, scrum reassignments).

## Output

The generated file (`.context/people.md`) contains per-scrum tables with:
- Name and role
- Email address
- Jira username
- GitHub username

This file is gitignored because it contains email addresses. Each user of this repo should run `/populate-people` to generate their own copy.
