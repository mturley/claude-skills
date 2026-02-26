# /export

Exports Claude Code sessions to readable markdown files. Converts the raw JSONL session format into clean documentation.

## Installation

Place the skill at `~/.claude/skills/export/` (symlink or copy).

## Usage

Run `/export` to export the current conversation to `~/.claude/exported-sessions/claude-session-YYYY-MM-DD-HHMMSS.md`.

The skill will:
1. Find the current session file based on your working directory
2. Run the Python export script to convert JSONL to markdown
3. Report where the file was saved and how many messages it contains
4. Offer to commit and push to the `~/.claude` git repository

## Output Format

The exported markdown includes:
- All user messages (with IDE/system tags stripped)
- All assistant responses
- User answers to AskUserQuestion prompts
- User feedback when rejecting plan mode
- Plan content (in collapsible details blocks)
- Tool calls summarized (tool name, key parameters)
- Timestamps for each message
