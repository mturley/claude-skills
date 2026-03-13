# /claude-activity

Summarizes what was accomplished across all Claude Code sessions for a given day by scanning session JSONL files from `~/.claude/projects/`.

## Installation

Place the skill at `~/.claude/skills/claude-activity/` (symlink or copy).

## Usage

```
/claude-activity              # summarize today's sessions
/claude-activity 2026-03-13   # summarize a specific date
```

The skill runs a Python script that extracts user messages from all session files modified on the target date, then Claude summarizes the raw data into a concise accomplishment report.

## How it works

1. **`extract-sessions.py`** scans `~/.claude/projects/*/` for `.jsonl` session files modified on the target date
2. Extracts user messages, filtering out system/XML content and condensing skill invocations
3. Groups sessions by project (resolving Claude's encoded project directory names back to real paths)
4. Outputs a structured markdown summary with timestamps
5. Claude reads the output and writes a human-friendly summary of accomplishments

## Design notes

- The Python script does the heavy lifting of parsing JSONL files, so Claude doesn't need to read large session files directly
- Project directory names (e.g. `-Users-mturley-git-rhoai-work`) are resolved back to readable paths by checking which reconstructed paths exist on disk
- Timestamps are converted from UTC (as stored in session files) to local time
- Messages from prior days in resumed sessions are filtered out
- Skill invocations are condensed to show just the skill name and arguments
