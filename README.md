# Claude Code Skills

Custom skills (slash commands) for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that I'm experimenting with. Some of these may be useful to others, but some are team-specific workflows (e.g., `/create-jira` is tailored to the Green scrum's feature areas).

## Compatibility

These skills also work with [Cursor](https://cursor.com) and other tools that support the [Agent Skills](https://agentskills.io/) standard. Cursor supports `~/.claude/skills/` as a [compatible path](https://cursor.com/docs/context/skills).

## Installation

Clone this repo and symlink individual skills and the `.mcp-usage` directory to your Claude Code skills directory:

```bash
git clone git@github.com:mturley/claude-skills.git ~/git/claude-skills
mkdir -p ~/.claude/skills
ln -s ~/git/claude-skills/export ~/.claude/skills/export
ln -s ~/git/claude-skills/review ~/.claude/skills/review
ln -s ~/git/claude-skills/create-jira ~/.claude/skills/create-jira
ln -s ~/git/claude-skills/.mcp-usage ~/.claude/skills/.mcp-usage
```

**Important:** Make sure to symlink the `.mcp-usage` directory—it contains shared MCP documentation needed by some skills.

Alternatively, you can symlink the entire repo (though this includes git history):
```bash
ln -s ~/git/claude-skills ~/.claude/skills
```

Or copy individual folders to `~/.claude/skills/`.

## Skills

See each skill directory's README.md for more information.

### [/export](export/)

Exports Claude Code sessions to readable markdown files. Converts the raw JSONL session format into clean documentation.

### [/review](review/)

Reviews pull requests by checking out the branch and analyzing changes file-by-file.

### [/create-jira](create-jira/)

Creates Jira issues in the RHOAIENG project. This skill is specific to the Red Hat AI (RHOAI) Dashboard team's Green scrum but serves as an example of a team-specific skill that gathers context from conversation history and drafts structured issues.

## Skills in Other Projects

I've also created skills in other repositories:

- [/model-registry-upstream-sync](https://github.com/opendatahub-io/odh-dashboard/blob/main/.claude/skills/model-registry-upstream-sync/SKILL.md) - Orchestrates syncing upstream changes from the kubeflow/model-registry repository, handling branch creation, merge conflicts, tests, and PR creation.

## MCP Usage Reference

The [`.mcp-usage/`](.mcp-usage/) directory contains shared documentation for using Model Context Protocol (MCP) servers with Claude Code. This includes field references, usage patterns, and gotchas for various MCPs used by skills in this repo.

See [`.mcp-usage/README.md`](.mcp-usage/README.md) for available MCP documentation.

To make this documentation available to Claude in all sessions:

1. **Symlink the directory** (makes files physically accessible):
   ```bash
   ln -s ~/git/claude-skills/.mcp-usage ~/.claude/skills/.mcp-usage
   ```

2. **Add a generic MCP reference in your global `~/.claude/CLAUDE.md`** (tells Claude to check the directory):

   ```markdown
   # MCP Server Operations

   Before using any MCP server tools, check `~/.claude/skills/.mcp-usage/` for a corresponding
   documentation file. These files contain server-specific information like custom field IDs,
   format requirements, and gotchas.
   ```

   This single instruction works for all MCP servers (Jira, Puppeteer, etc.), telling Claude to
   look in the `.mcp-usage/` directory for relevant documentation when using any MCP.

This ensures Claude proactively uses this documentation in all sessions, not just when using skills.

## Creating Your Own Skills

Each skill is a folder containing a `SKILL.md` file with instructions for Claude. See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for details on the skill format.
