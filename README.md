# Claude Code Skills

Custom skills (slash commands) for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that I'm experimenting with. Some of these may be useful to others, but some are team-specific workflows (e.g., `/create-jira` is tailored to the Green scrum's feature areas).

## Compatibility

These skills also work with [Cursor](https://cursor.com) and other tools that support the [Agent Skills](https://agentskills.io/) standard. Cursor supports `~/.claude/skills/` as a [compatible path](https://cursor.com/docs/context/skills).

## Installation

1. Clone the repo:
   ```bash
   git clone git@github.com:mturley/claude-skills.git ~/git/claude-skills
   ```

2. Symlink individual skills and shared directories to your Claude Code skills directory:
   ```bash
   mkdir -p ~/.claude/skills

   # Required shared directories (see skill descriptions for which ones each skill needs):
   ln -s ~/git/claude-skills/.context ~/.claude/skills/.context
   ln -s ~/git/claude-skills/.shared-scripts ~/.claude/skills/.shared-scripts

   # Link the skills you want to use:
   ln -s ~/git/claude-skills/branch-worktree ~/.claude/skills/branch-worktree
   ln -s ~/git/claude-skills/export ~/.claude/skills/export
   ln -s ~/git/claude-skills/pr-worktree ~/.claude/skills/pr-worktree
   ln -s ~/git/claude-skills/review ~/.claude/skills/review
   ln -s ~/git/claude-skills/create-jira ~/.claude/skills/create-jira
   ln -s ~/git/claude-skills/reviews-status ~/.claude/skills/reviews-status
   ln -s ~/git/claude-skills/sprint-status ~/.claude/skills/sprint-status
   ln -s ~/git/claude-skills/epic-status ~/.claude/skills/epic-status
   ```
   - **`.context/`** contains shared context files (MCP documentation, team data) needed by some skills.
   - **`.shared-scripts/`** contains shared Python utilities and scripts used by multiple skills.

   Alternatively, you can symlink the entire repo, though this includes git history and means any other skills you add would become untracked files in this repo:
   ```bash
   ln -s ~/git/claude-skills ~/.claude/skills
   ```

   If you prefer, you can copy individual folders to `~/.claude/skills/` instead of using symlinks.

3. **(Optional)** Add a generic reference to the `.context` directory in your global `~/.claude/CLAUDE.md` so Claude proactively checks for MCP documentation in all sessions, not just when using skills:
   ```markdown
   # MCP Server Operations

   Before using any MCP server tools, check `~/.claude/skills/.context/` for a corresponding
   documentation file (named `<server>-mcp.md`). These files contain server-specific information
   like custom field IDs, format requirements, and gotchas.
   ```

## Skills

See each skill directory's README.md for more information.

### [/export](export/)

Exports Claude Code sessions to readable markdown files. Converts the raw JSONL session format into clean documentation.

### [/review](review/)

Reviews pull requests by checking out the branch and analyzing changes file-by-file. Requires a clean working tree.

### [/branch-worktree](branch-worktree/)

Creates an isolated git worktree for a new branch and opens it in a new editor window. Useful for starting work on a new feature or fix without affecting your current working tree.

### [/pr-worktree](pr-worktree/)

Creates an isolated git worktree for a pull request and opens it in a new editor window. Use with `/review` to review PRs without affecting your working tree.

### [/reviews-status](reviews-status/)

Shows the review status of open PRs across your work, your team's sprint, and your scrum members, cross-referenced with RHOAIENG Jira issues. Highlights where your action is needed with emoji indicators and links to Jira issues with type, status, sprint, and epic.
Requires: `.context/`, `.shared-scripts/`

(`/reviews-status` is specific to RHOAI Dashboard team's Green Scrum, but could be generalized)

### [/sprint-status](sprint-status/)

Shows the current Green sprint status with all tickets grouped by workflow status (Review, In Progress, Backlog, Closed/Resolved). Each section includes a table with Jira issue details (story points, assignee, blocked status, epic) and linked GitHub PR metadata (review status, CI status).
Requires: `.context/`, `.shared-scripts/`

(`/sprint-status` is specific to RHOAI Dashboard team's Green Scrum, but could be generalized)

### [/epic-status](epic-status/)

Shows all issues in a selected epic, discovered from the current Green sprint. Displays Jira issue details and GitHub PR metadata grouped by status, with sprint information for each issue.
Requires: `.context/`, `.shared-scripts/`

(`/epic-status` is specific to RHOAI Dashboard team's Green Scrum, but could be generalized)

### [/create-jira](create-jira/)

Creates Jira issues in the RHOAIENG project. This skill is specific to the Red Hat AI (RHOAI) Dashboard team's Green scrum but serves as an example of a team-specific skill that gathers context from conversation history and drafts structured issues.
Requires: `.context/`

(`/create-jira` is specific to the RHOAI Dashboard team's Green Scrum, but could be generalized)

### [/populate-people](populate-people/)

Generates or updates `.context/people.md` with RHOAI Dashboard team member information by cross-referencing Confluence, Jira, and GitHub. Useful for populating team context that other skills can reference.

## Skills in Other Projects

I've also created skills in other repositories:

- [/model-registry-upstream-sync](https://github.com/opendatahub-io/odh-dashboard/blob/main/.claude/skills/model-registry-upstream-sync/SKILL.md) - Orchestrates syncing upstream changes from the kubeflow/model-registry repository, handling branch creation, merge conflicts, tests, and PR creation.

## Creating Your Own Skills

Each skill is a folder containing a `SKILL.md` file with instructions for Claude. See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for details on the skill format.
