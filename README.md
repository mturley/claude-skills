# Claude Code Skills

Custom skills (slash commands) for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that I'm experimenting with. Some of these may be useful to others, but some are team-specific workflows (e.g., `/create-jira` is tailored to the Green scrum's feature areas).

## Compatibility

These skills also work with [Cursor](https://cursor.com), which supports `~/.claude/skills/` as a [compatible path](https://cursor.com/docs/context/skills).

## Installation

Clone this repo and symlink individual skills to your Claude Code skills directory:

```bash
git clone git@github.com:mturley/claude-skills.git ~/git/claude-skills
mkdir -p ~/.claude/skills
ln -s ~/git/claude-skills/export ~/.claude/skills/export
ln -s ~/git/claude-skills/review ~/.claude/skills/review
```

Or copy individual skill folders to `~/.claude/skills/`.

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

## Creating Your Own Skills

Each skill is a folder containing a `SKILL.md` file with instructions for Claude. See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for details on the skill format.
