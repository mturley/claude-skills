# Activity

Show a summary of your personal activity on GitHub and Jira for a given day.

**Optional argument:** A date (e.g. `yesterday`, `March 3`, `2026-03-05`). Defaults to today.

**Technical Reference:** For Jira field IDs and formats, see [`../.context/jira-mcp.md`](../.context/jira-mcp.md)

**Helper Script:** `~/.claude/skills/activity/fetch-github-activity.py` — fetches GitHub activity via the Events API (`/users/{username}/events`). Pass `{"username": "...", "date": "YYYY-MM-DD"}` on stdin, get back `{prs_opened, prs_merged, reviews, jira_search_paths}`.

**Helper Script:** `~/.claude/skills/activity/fetch-pr-titles.py` — fetches PR titles from GitHub API in parallel. Pass a JSON array of `{owner, repo, number}` on stdin, get back `{"owner/repo/pull/number": "title", ...}`.

**Helper Script:** `~/.claude/skills/activity/render-activity-report.py` — combines GitHub and Jira data into a rendered markdown report. Uses shared `jira_utils.py` and `format_utils.py` for parsing and formatting.

## Instructions

### Phase 0: Resolve Date and User Context

1. Parse the argument into a `YYYY-MM-DD` date string. If no argument is given, use today's date.
2. Compute the next day's date as `YYYY-MM-DD` (for the Jira upper bound).
3. Read `../.context/people.md` and find the **About Me** section to get the user's GitHub username and Jira username.

### Phase 1: Gather Activity

Run ALL of the following in parallel in a single tool-call round:

1. **Fetch GitHub activity:** Pipe the username and date to `fetch-github-activity.py`:
   ```bash
   echo '{"username":"<github_username>","date":"<YYYY-MM-DD>"}' | python3 ~/.claude/skills/activity/fetch-github-activity.py
   ```

2. **Fetch Jira activity:** Search for issues where the user is assignee or reporter, updated on the target date:
   ```
   project = RHOAIENG AND (assignee = <jira_username> OR reporter = <jira_username>) AND updated >= "<YYYY-MM-DD>" AND updated < "<next_day_YYYY-MM-DD>"
   ```
   Run as a single `jira_searchIssues` call with `maxResults: 100`.

### Phase 2: Cross-reference and PR Titles

After Phase 1 completes, collect PR URLs from Jira issues (the `customfield_12310220` / `pr_urls` field) that are NOT already represented in the GitHub activity data (`prs_opened`, `prs_merged`, `reviews`). Parse these URLs to get `{owner, repo, number}` objects — these are PRs that need titles fetched.

Run ALL of the following in parallel in a single tool-call round:

1. **Jira cross-reference** _(skip if `jira_search_paths` is empty)_: Search for Jira issues linked to the GitHub PRs:
   ```
   project = RHOAIENG AND (cf[12310220] ~ "path1" OR cf[12310220] ~ "path2" OR ...)
   ```
   Run as a single `jira_searchIssues` call.

2. **Fetch PR titles** _(skip if no unknown PRs)_: Pipe the list of PRs needing titles to `fetch-pr-titles.py`:
   ```bash
   echo '[{"owner":"org","repo":"name","number":123},...]' | python3 ~/.claude/skills/activity/fetch-pr-titles.py
   ```

### Phase 3: Render Report

Assemble all data and pipe through `render-activity-report.py`. Use a heredoc for the payload:

```bash
cat <<'EOF' | python3 ~/.claude/skills/activity/render-activity-report.py
{"date":"<YYYY-MM-DD>","github":<github_activity_json>,"jira_updated_raw":<raw_jira_result_or_null>,"jira_crossref_raw":<raw_crossref_result_or_null>,"pr_titles":<pr_titles_or_empty_object>}
EOF
```

The input JSON format:
- `date`: the target date as `"YYYY-MM-DD"`
- `github`: the full output from `fetch-github-activity.py`
- `jira_updated_raw`: the raw Jira search result from Phase 1 step 2 (or `null` if no results)
- `jira_crossref_raw`: the raw Jira cross-ref result from Phase 2 (or `null` if skipped)
- `pr_titles`: the output from `fetch-pr-titles.py` (or `{}` if skipped) — maps `"owner/repo/pull/number"` to title strings. The render script also builds titles from the GitHub activity data, so this only needs PRs not already in that data.

When a Jira tool result is persisted to a file (output too large for inline), read the file content and include it as the value. The scripts auto-detect the MCP wrapper format.

**IMPORTANT:** Output the rendered report directly as text in the chat so the user can read it. Do NOT just leave the output in the tool result — the user cannot see tool results. Copy the full report output and send it as your response text.

## Report Sections

The report is grouped by activity type:

- **Shipped** — PRs merged that day, with linked Jira issues shown as sub-items
- **Opened** — PRs opened that day (even if also merged), with linked Jira issues
- **Reviewed** — Reviews and comments on others' PRs (formal reviews, line comments, and general comments), with linked Jira issues
- **Jira Activity** — Issues where user is assignee or reporter that were updated that day, with linked PRs shown as sub-items. Issues created that day are tagged *Created today*.

Empty sections are omitted.

## Limitations

- **GitHub Events API** is limited to the last 90 days and 300 most recent events. For older dates, results may be incomplete.
- **Jira activity** only captures issues where the user is assignee or reporter. Issues the user commented on without being assignee or reporter are not included.

## Important Notes

- Maximize parallel tool calls — run everything listed in each phase in a SINGLE tool-call round
- The report is read-only — do not modify any PRs or Jira issues
- **Never use inline Python** (`cat <<'PYEOF' | python3` with arbitrary code). All Bash commands must pipe to the skill helper scripts so they match the auto-approved permission patterns `echo *| python3 *activity/*`, `cat *| python3 *activity/*`, `echo *| python3 *.shared-scripts/*`, and `cat *| python3 *.shared-scripts/*`.
- For large JSON payloads that may exceed shell argument limits, use a heredoc piped to the script.
- When a Jira tool result is persisted to a file (output too large), read the file and include its content in the JSON payload.
