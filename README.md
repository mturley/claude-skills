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
   ln -s ~/git/claude-skills/pr-worktree ~/.claude/skills/pr-worktree
   ln -s ~/git/claude-skills/review ~/.claude/skills/review
   ln -s ~/git/claude-skills/create-jira ~/.claude/skills/create-jira
   ln -s ~/git/claude-skills/reviews-status ~/.claude/skills/reviews-status
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

Reviews pull requests by checking out the branch and analyzing changes file-by-file. Requires a clean working tree.

### [/pr-worktree](pr-worktree/)

Creates an isolated git worktree for a pull request and opens it in a new editor window. Use with `/review` to review PRs without affecting your working tree.

### [/reviews-status](reviews-status/)

Shows the review status of open PRs across your work, your team's sprint, and your scrum members, cross-referenced with RHOAIENG Jira issues. Highlights where your action is needed with emoji indicators and links to Jira issues with type, status, sprint, and epic.

(`/reviews-status` is specific to RHOAI Dashboard team's Green Scrum, but could be generalized)

### [/create-jira](create-jira/)

Creates Jira issues in the RHOAIENG project. This skill is specific to the Red Hat AI (RHOAI) Dashboard team's Green scrum but serves as an example of a team-specific skill that gathers context from conversation history and drafts structured issues.

(`/create-jira` is specific to the RHOAI Dashboard team's Green Scrum, but could be generalized)

### [/populate-people](populate-people/)

Generates or updates `.context/people.md` with RHOAI Dashboard team member information by cross-referencing Confluence, Jira, and GitHub. Useful for populating team context that other skills can reference.

## Skills in Other Projects

I've also created skills in other repositories:

- [/model-registry-upstream-sync](https://github.com/opendatahub-io/odh-dashboard/blob/main/.claude/skills/model-registry-upstream-sync/SKILL.md) - Orchestrates syncing upstream changes from the kubeflow/model-registry repository, handling branch creation, merge conflicts, tests, and PR creation.

## Creating Your Own Skills

Each skill is a folder containing a `SKILL.md` file with instructions for Claude. See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for details on the skill format.
