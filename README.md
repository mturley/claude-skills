# Claude Code Skills

Custom skills (slash commands) for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that I'm experimenting with. Some of these may be useful to others, but some are team-specific workflows (e.g., `/create-jira` is tailored to the Green scrum's feature areas).

## Compatibility

These skills also work with [Cursor](https://cursor.com) and other tools that support the [Agent Skills](https://agentskills.io/) standard. Cursor supports `~/.claude/skills/` as a [compatible path](https://cursor.com/docs/context/skills).

## Installation

1. Clone the repo:
   ```bash
   git clone git@github.com:mturley/claude-skills.git ~/git/claude-skills
   ```

2. Symlink individual skills and the `.mcp-usage` directory to your Claude Code skills directory:
   ```bash
   mkdir -p ~/.claude/skills

   # Required for some skills:
   ln -s ~/git/claude-skills/.mcp-usage ~/.claude/skills/.mcp-usage

   # Link the skills you want to use:
   ln -s ~/git/claude-skills/export ~/.claude/skills/export
   ln -s ~/git/claude-skills/review ~/.claude/skills/review
   ln -s ~/git/claude-skills/create-jira ~/.claude/skills/create-jira
   ln -s ~/git/claude-skills/review-status ~/.claude/skills/review-status
   ```
   Make sure to symlink the `.mcp-usage` directory—it contains shared MCP documentation needed by some skills. This is not part of the Agent Skills standard, it is this repo's way of sharing info across skills.

   Alternatively, you can symlink the entire repo, though this includes git history and means any other skills you add would become untracked files in this repo:
   ```bash
   ln -s ~/git/claude-skills ~/.claude/skills
   ```

   If you prefer, you can copy individual folders to `~/.claude/skills/` instead of using symlinks.

3. **(Optional)** Add a generic reference to the `.mcp-usage` directory in your global `~/.claude/CLAUDE.md` so Claude proactively checks for MCP documentation in all sessions, not just when using skills:
   ```markdown
   # MCP Server Operations

   Before using any MCP server tools, check `~/.claude/skills/.mcp-usage/` for a corresponding
   documentation file. These files contain server-specific information like custom field IDs,
   format requirements, and gotchas.
   ```

## Skills

See each skill directory's README.md for more information.

### [/export](export/)

Exports Claude Code sessions to readable markdown files. Converts the raw JSONL session format into clean documentation.

### [/review](review/)

Reviews pull requests in an isolated git worktree, allowing multiple PRs to be reviewed simultaneously without affecting your working tree.

### [/create-jira](create-jira/)

Creates Jira issues in the RHOAIENG project. This skill is specific to the Red Hat AI (RHOAI) Dashboard team's Green scrum but serves as an example of a team-specific skill that gathers context from conversation history and drafts structured issues.

### [/review-status](review-status/)

Generates a dashboard of open PRs you're involved with, cross-referenced with RHOAIENG Jira issues. Shows up to four tables (your PRs, PRs you've reviewed/commented on, sprint Review PRs, and unlinked team member PRs) with review status, CI status, linked Jira issues with type/status/sprint/epic, and highlights where your action is needed.

### [/populate-people](populate-people/)

Generates or updates `.context/people.md` with RHOAI Dashboard team member information by cross-referencing Confluence, Jira, and GitHub. Useful for populating team context that other skills can reference.

## Skills in Other Projects

I've also created skills in other repositories:

- [/model-registry-upstream-sync](https://github.com/opendatahub-io/odh-dashboard/blob/main/.claude/skills/model-registry-upstream-sync/SKILL.md) - Orchestrates syncing upstream changes from the kubeflow/model-registry repository, handling branch creation, merge conflicts, tests, and PR creation.

## Creating Your Own Skills

Each skill is a folder containing a `SKILL.md` file with instructions for Claude. See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for details on the skill format.
