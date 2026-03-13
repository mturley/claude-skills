# Jira Activity

**This skill is obsolete.** The [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app now provides the same information in a persistent, auto-refreshing dashboard. Before proceeding, tell the user about pr-reviews-dashboard and recommend using it instead. Then use AskUserQuestion to ask if they want to proceed with this skill anyway.

---

Show a chronological timeline of your Jira activity (changelog actions and comments) over a configurable time period, rendered with issue type and priority emojis, hyperlinked Jira issues and PRs, and times converted to Eastern Time.

**Optional argument:** Number of days to look back (default: 7). Example: `/jira-activity 14`

**Technical Reference:** For Jira field IDs and formats, see [`../.context/jira-mcp.md`](../.context/jira-mcp.md)

**Helper Script:** `~/.claude/skills/jira-activity/discover-issues.py` — deduplicates issue keys from search result files. Accepts `--assignee`, `--watcher`, `--reporter`, `--commenter` file path args.

**Helper Script:** `~/.claude/skills/jira-activity/render-activity.py` — extracts a user's changelog actions and comments from search result files and comment files, converts timestamps to the target timezone, and renders a markdown timeline with merged consecutive rows.

## Instructions

### Phase 1: Search & Discover

Run ALL of the following in parallel in a single tool-call round:

1. **Read people.md:** Read `../.context/people.md` to find the current user's Jira username (e.g. `mikejturley`) and Jira key (e.g. `mturley`). Look up the person matching the current GitHub user.

2. **Run 4 JQL searches** to find issues the user touched in the last N days (default 7, or the user-specified argument). Each should use `maxResults: 50` and `expand: ["changelog"]`:
   - **Assignee:** `project = RHOAIENG AND assignee = {jira_username} AND updated >= -{days}d`
   - **Watcher:** `project = RHOAIENG AND watcher = {jira_username} AND updated >= -{days}d`
   - **Reporter:** `project = RHOAIENG AND reporter = {jira_username} AND updated >= -{days}d`
   - **Commenter:** `project = RHOAIENG AND issueFunction in commented("by {jira_username} after -{days}d")`

   If the `issueFunction in commented()` query returns an error (not all Jira instances support it), skip it and continue without commenter data.

   **All 4 search results will be large and auto-persist to files.** Note the persisted file path for each result.

After Phase 1 calls complete, run `discover-issues.py` with the persisted file paths:

```bash
python3 ~/.claude/skills/jira-activity/discover-issues.py \
  --assignee /path/to/assignee-result.json \
  --watcher /path/to/watcher-result.json \
  --reporter /path/to/reporter-result.json \
  --commenter /path/to/commenter-result.json
```

This outputs:
- `issue_keys`: all unique issue keys found (for reference)
- `commented_keys`: issue keys where the user commented (fetch comments for these)
- `total`: count of unique issues

### Phase 2: Fetch Comments & Render

1. **Fetch comments:** For each issue key in `commented_keys`, call `jira_getIssueComments` in parallel.

   For each comment result:
   - If persisted to a file, note the file path
   - If returned inline, write it to a temp file: `echo '<result_json>' > /tmp/comments-RHOAIENG-XXXXX.json`

2. **Render timeline:** Compute the cutoff date (today minus N days) and run:

```bash
python3 ~/.claude/skills/jira-activity/render-activity.py \
  --username-keys mikejturley mturley \
  --timezone America/New_York \
  --cutoff 2026-03-02 \
  --today 2026-03-09 \
  --search-files /path/to/assignee.json /path/to/watcher.json /path/to/reporter.json /path/to/commenter.json \
  --comment-files RHOAIENG-51543=/path/to/comments1.json RHOAIENG-51556=/path/to/comments2.json
```

CLI args:
- `--username-keys`: Jira username and key variants for the user (from people.md). Include both the `name` (login username) and the `key` (internal Jira key). If you discover additional identifiers (e.g. `JIRAUSER` IDs) in the API responses, include those too.
- `--timezone`: IANA timezone name (default `"America/New_York"`)
- `--cutoff`: Start date for the activity window as `YYYY-MM-DD`
- `--today`: Today's date as `YYYY-MM-DD`
- `--search-files`: Paths to the 4 persisted search result files (from Phase 1). Each contains issues with changelogs. The script deduplicates across files.
- `--comment-files`: Comment file specs as `ISSUE_KEY=/path/to/file.json` (one per commented issue). Omit if no commented keys.

**IMPORTANT:** Output the rendered report directly as text in the chat so the user can read it. Do NOT just leave the output in the tool result — the user cannot see tool results. Copy the full report output and send it as your response text.

## Output Format

The timeline is organized by day, with a table per day. Columns:

| Column | Content |
|--------|---------|
| Time (ET) | 12-hour AM/PM format, converted to Eastern Time |
| Assignee | Display name of the issue's assignee. Blank when same as previous row (visual merge). |
| Issue | Hyperlinked `[KEY](url) — Full Issue Title`. Blank when same as previous row (visual merge). |
| Type | Emoji + type name (🟥 Bug, 🟩 Story, ☑️ Task, ⚡ Epic, etc.) |
| Priority | Emoji + priority name (⛔ Blocker, 🔺 Critical, 🔶 Major, 🔵 Normal, etc.) |
| Action | What changed: field transitions, status changes, comments, PR links, etc. |

Description changes are summarized as "Updated description" to avoid verbose diffs. Comment bodies are shown as a one-line preview.

## Important Notes

- Maximize parallel tool calls — run everything listed in each phase in a SINGLE tool-call round
- The report is read-only — do not modify any Jira issues
- Search results with `expand: ["changelog"]` are large and will auto-persist to files. This is expected — the helper scripts read directly from those files. Never try to read persisted files back into context; just pass the file paths to the scripts.
- For comment results that come back inline (not persisted), write them to temp files before passing to the render script.
- **Never use inline Python** (`cat <<'PYEOF' | python3` with arbitrary code). All Bash commands must call the skill helper scripts directly.
