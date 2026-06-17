---
name: diff-review
description: Launch vibediff for interactive code review with inline comments, then address the feedback. Use when the user wants to review changes before committing, when asked to review a diff, or for standalone code reviews of uncommitted changes.
---

# Interactive Code Review with vibediff

Launch [vibediff](https://github.com/malvex/vibediff) to let the user review the current git diff in a browser-based UI with inline commenting. After the user finishes, parse their comments and address each one.

## Prerequisites

- `vibediff` CLI installed: `brew install malvex/tap/vibediff`

## Workflow

### Phase 1: Launch vibediff

1. Run the start script in the background:
   ```
   ~/.claude/skills/diff-review/start.sh
   ```
   Use `run_in_background: true` on the Bash tool. Save the output file path.

2. Read the output file to get the PID from the `VIBEDIFF_PID=<pid>` line and the port from the `VIBEDIFF_PORT=<port>` line. If the output instead contains an error (e.g. "command not found"), tell the user:
   ```
   vibediff is not installed. Install it with:

     brew install malvex/tap/vibediff

   Then run /diff-review again.
   ```
   Then **stop**.

3. Tell the user:
   ```
   vibediff is running — it should have opened in your browser.
   Review the diff and leave inline comments, then tell me when you're done.
   Say "abort" if you want to cancel without processing comments.
   ```

4. **Wait for the user's response.** Do not proceed until the user says they are done or aborts.

### Phase 2: Collect Comments

When the user says they are done:

1. Run the stop script with the PID, port, and output file path:
   ```
   ~/.claude/skills/diff-review/stop.sh <VIBEDIFF_PID> <VIBEDIFF_PORT> <output_file_path>
   ```

2. Parse the JSON array of comments from the output. Each comment has:
   - `file` — the file path
   - `line` / `lineEnd` — the line range
   - `content` — the comment text

3. If there are no comments, tell the user no comments were found and stop.

### Phase 2 (Abort Path)

If the user says "abort" or wants to cancel:

1. Run the abort script with the PID and port:
   ```
   ~/.claude/skills/diff-review/abort.sh <VIBEDIFF_PID> <VIBEDIFF_PORT>
   ```
2. **Stop** — do not process any comments.

### Phase 3: Address Comments

1. Present a summary of all comments to the user, listing each with its file, line number, and content.

2. For each comment, read the relevant file and lines, understand the feedback, and address it. This may involve:
   - Making code changes
   - Explaining a decision (if the comment is a question)
   - Asking the user for clarification (if the comment is ambiguous)

3. After addressing all comments, summarize what was changed.
