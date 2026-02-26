# Claude Code Skills

Custom skills (slash commands) for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

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

### /export

Exports Claude Code sessions to readable markdown files. Converts the raw JSONL session format into clean documentation.

### /review

Reviews pull requests by checking out the branch and analyzing changes file-by-file.

### /create-jira

Creates Jira issues in the RHOAIENG project. This skill is specific to the Red Hat AI (RHOAI) Dashboard team but serves as an example of a team-specific skill that gathers context from conversation history and drafts structured issues.

## Creating Your Own Skills

Each skill is a folder containing a `SKILL.md` file with instructions for Claude. See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for details on the skill format.
