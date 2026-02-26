# Export Session

Export the current Claude Code session to a readable markdown file.

## Usage

Run `/export` to export the current conversation to `~/.claude/exported-sessions/claude-session-YYYY-MM-DD-HHMMSS.md`.

## Instructions

1. **Find the current session file**

   Session files are stored in `~/.claude/projects/<project-path>/`. Find the most recently modified `.jsonl` file:

   ```bash
   ls -t ~/.claude/projects/*/. 2>/dev/null | head -1
   ```

   Or determine the project path from the current working directory by replacing `/` with `-` and prepending `-`.

2. **Run the export script**

   Generate a timestamped filename and run the Python script:

   ```bash
   python3 ~/.claude/skills/export/export-session.py <session-file> ~/.claude/exported-sessions/claude-session-$(date +%Y-%m-%d-%H%M%S).md
   ```

3. **Report the result**

   Tell the user where the file was saved and how many messages it contains.

4. **Offer to commit and push**

   Ask the user if they want to commit and push the exported session file to the ~/.claude git repository. If yes:
   - `cd ~/.claude`
   - `git add exported-sessions/<filename>`
   - Commit with message: "Add exported session: <filename>"
   - `git push`

## Finding the Session File

The session file path follows this pattern:
- Project directory: `~/.claude/projects/-Users-<username>-<path-to-repo>`
- Session file: Most recently modified `.jsonl` file in that directory

For example, if working in `/Users/mturley/git/odh-dashboard`, the sessions are in:
`~/.claude/projects/-Users-mturley-git-odh-dashboard/`

To find the current session:
```bash
ls -t ~/.claude/projects/-Users-mturley-git-odh-dashboard/*.jsonl | head -1
```

## Output Format

The exported markdown includes:
- All user messages (with IDE/system tags stripped)
- All assistant responses
- User answers to AskUserQuestion prompts
- User feedback when rejecting plan mode (ExitPlanMode)
- Full plan content when written to plan files (in collapsible details)
- Approved plan content when ExitPlanMode succeeds (in collapsible details)
- Tool calls summarized (tool name, key parameters)
- Timestamps for each message
- Clean markdown formatting with headers and separators
