# Jira Activity

Show a chronological timeline of your Jira activity (changelog actions and comments) over a configurable time period, rendered with issue type and priority emojis, hyperlinked Jira issues and PRs, and times converted to Eastern Time.

**Optional argument:** Number of days to look back (default: 7). Example: `/jira-activity 14`

**Technical Reference:** For Jira field IDs and formats, see [`../.context/jira-mcp.md`](../.context/jira-mcp.md)

**Helper Script:** `~/.claude/skills/jira-activity/discover-issues.py` — deduplicates issue keys from multiple Jira search results. Pass raw results on stdin as JSON, get back `{issue_keys, commented_keys, total}`.

**Helper Script:** `~/.claude/skills/jira-activity/render-activity.py` — extracts a user's changelog actions and comments from raw getIssue/getIssueComments data, converts timestamps to the target timezone, and renders a markdown timeline with merged consecutive rows.

## Instructions

### Phase 1: Discover Issues

Run ALL of the following in parallel in a single tool-call round:

1. **Read people.md:** Read `../.context/people.md` to find the current user's Jira username (e.g. `mikejturley`) and Jira key (e.g. `mturley`). Look up the person matching the current GitHub user.

2. **Run 4 JQL searches** to find issues the user touched in the last N days (default 7, or the user-specified argument). Each should use `maxResults: 50`:
   - **Assignee:** `project = RHOAIENG AND assignee = {jira_username} AND updated >= -{days}d`
   - **Watcher:** `project = RHOAIENG AND watcher = {jira_username} AND updated >= -{days}d`
   - **Reporter:** `project = RHOAIENG AND reporter = {jira_username} AND updated >= -{days}d`
   - **Commenter:** `project = RHOAIENG AND issueFunction in commented("by {jira_username} after -{days}d")`

   If the `issueFunction in commented()` query returns an error (not all Jira instances support it), skip it and continue without commenter data.

After Phase 1 calls complete, pipe all 4 raw results to `discover-issues.py`:

```bash
cat <<'EOF' | python3 ~/.claude/skills/jira-activity/discover-issues.py
{"assignee": <raw_assignee_result>, "watcher": <raw_watcher_result>, "reporter": <raw_reporter_result>, "commenter": <raw_commenter_result>}
EOF
```

When a Jira tool result is persisted to a file (output too large for inline), read the file content and include it as the value. The script auto-detects the MCP wrapper format.

This outputs:
- `issue_keys`: all unique issue keys to fetch changelogs for
- `commented_keys`: issue keys where the user commented (fetch comments for these)
- `total`: count of unique issues

### Phase 2: Fetch Changelogs and Comments

Run ALL of the following in parallel in a single tool-call round:

1. **Fetch changelogs:** For each issue key in `issue_keys`, call `jira_getIssue` with `expand: "changelog"`.
2. **Fetch comments:** For each issue key in `commented_keys`, call `jira_getIssueComments`.

Make all calls in parallel. When a tool result is persisted to a file (output too large for inline), read the file content and include it in the Phase 3 input.

### Phase 3: Render Timeline

Compute the cutoff date: today minus N days (the lookback period from the argument).

Assemble all data and pipe to `render-activity.py`. Use a heredoc for the payload:

```bash
cat <<'EOF' | python3 ~/.claude/skills/jira-activity/render-activity.py
{
  "username_keys": ["mikejturley", "mturley"],
  "timezone": "America/New_York",
  "cutoff": "2026-03-02",
  "today": "2026-03-09",
  "issues": {
    "RHOAIENG-51543": <raw_getIssue_result>,
    "RHOAIENG-27992": <raw_getIssue_result>
  },
  "comments": {
    "RHOAIENG-51543": <raw_getIssueComments_result>
  }
}
EOF
```

Input fields:
- `username_keys`: Jira username and key variants for the user (from people.md). Include both the `name` (login username) and the `key` (internal Jira key). If you discover additional identifiers (e.g. `JIRAUSER` IDs) in the API responses, include those too.
- `timezone`: IANA timezone name (default `"America/New_York"`)
- `cutoff`: Start date for the activity window as `"YYYY-MM-DD"`
- `today`: Today's date as `"YYYY-MM-DD"`
- `issues`: Map of issue key → raw `jira_getIssue` result (with changelog)
- `comments`: Map of issue key → raw `jira_getIssueComments` result (only for commented issues)

**IMPORTANT:** Output the rendered report directly as text in the chat so the user can read it. Do NOT just leave the output in the tool result — the user cannot see tool results. Copy the full report output and send it as your response text.

## Output Format

The timeline is organized by day, with a table per day. Columns:

| Column | Content |
|--------|---------|
| Time (ET) | 12-hour AM/PM format, converted to Eastern Time |
| Issue | Hyperlinked `[KEY](url) — Full Issue Title`. Blank when same as previous row (visual merge). |
| Type | Emoji + type name (🟥 Bug, 🟩 Story, ☑️ Task, ⚡ Epic, etc.) |
| Priority | Emoji + priority name (⛔ Blocker, 🔺 Critical, 🔶 Major, 🔵 Normal, etc.) |
| Action | What changed: field transitions, status changes, comments, PR links, etc. |

Description changes are summarized as "Updated description" to avoid verbose diffs. Comment bodies are shown as a one-line preview.

## Important Notes

- Maximize parallel tool calls — run everything listed in each phase in a SINGLE tool-call round
- The report is read-only — do not modify any Jira issues
- **Never use inline Python** (`cat <<'PYEOF' | python3` with arbitrary code). All Bash commands must pipe to the skill helper scripts so they match the auto-approved permission patterns `echo *| python3 *jira-activity/*`, `cat *| python3 *jira-activity/*`, `echo *| python3 *.shared-scripts/*`, and `cat *| python3 *.shared-scripts/*`.
- For large JSON payloads that may exceed shell argument limits, use a heredoc piped to the script.
- When a Jira tool result is persisted to a file (output too large), read the file and include its content in the JSON payload — the scripts auto-detect the MCP wrapper format.
