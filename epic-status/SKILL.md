# Epic Status

Show the status of all issues in a selected epic, discovered from the current Green sprint. Discovers which epics are referenced by sprint issues, asks which one to view, then fetches all issues in that epic across all sprints with Jira details and GitHub PR metadata.

**Technical Reference:** For Jira field IDs and formats, see [`../.context/jira-mcp.md`](../.context/jira-mcp.md)

**Helper Script:** `~/.claude/skills/epic-status/extract-epic-issues.py` — parses raw Jira epic search results and extracts all fields. Pass raw Jira on stdin, get back `{issues, pr_metadata_input, sprints}`.

**Helper Script:** `~/.claude/skills/.shared-scripts/fetch-pr-metadata.py` — fetches PR metadata in parallel via `gh api`. Pass a JSON array of `{owner, repo, number}` on stdin, get back metadata with review status.

## Instructions

### Phase 1: Discover Epics from Current Sprint

**Step 1a — Discover sprint name (parallel):**

Run ALL of the following in parallel in a single tool-call round:

1. **Discover the active Green sprint name:** Run a Jira search to find any one issue in the current Green sprint:
   ```
   project = RHOAIENG AND sprint in openSprints() AND labels = "dashboard-green-scrum"
   ```
   Run as a single `jira_searchIssues` call with `maxResults: 1`.

2. **Look up the current Jira user:** Read `../.context/people.md` and find the Green Scrum member matching the current GitHub user (to determine Jira username and GitHub username).

After the discovery query returns, pipe it through `extract-sprint-issues.py` to get the full sprint name:

```bash
echo '<raw_jira_result>' | python3 ~/.claude/skills/sprint-status/extract-sprint-issues.py --filter-sprint Green
```

Extract `sprint_full_name` from the output (e.g. `"Dashboard - Green-35"`).

**Step 1b — Fetch all sprint issues (sequential):**

Using the discovered `sprint_full_name`, run a targeted Jira search for all issues in that specific sprint:
```
project = RHOAIENG AND sprint = "<sprint_full_name>"
```
Run as a single `jira_searchIssues` call with `maxResults: 100`.

Pipe the result through `extract-sprint-issues.py`:

```bash
cat <<'EOF' | python3 ~/.claude/skills/sprint-status/extract-sprint-issues.py --filter-sprint Green
<raw_jira_result>
EOF
```

From the output, extract the `epic_keys` array. Also count how many issues reference each epic from the `issues` array to show counts in the selection prompt.

**Step 2 — Epic lookup (parallel):**

If `epic_keys` is non-empty, construct a single JQL query:
```
key in (RHOAIENG-27992, RHOAIENG-12345, ...)
```
Run as a single `jira_searchIssues` call. Extract the summary from each issue and shorten to a concise label (e.g., "Dashboard - OCI Compliant Storage layer for Model Registry" → "OCI Storage").

### Phase 2: User Selection

Present the discovered epics to the user using `AskUserQuestion`. Each option should show the epic key, short name, and number of issues in the current sprint:

Example options:
- `RHOAIENG-27992 — OCI Storage (8 issues in sprint)`
- `RHOAIENG-12345 — MCP Catalog (5 issues in sprint)`

If no epics were found in the sprint, inform the user and stop.

### Phase 3: Fetch Epic Issues

Run a single Jira search for all issues in the selected epic:
```
"Epic Link" = RHOAIENG-XXXXX
```
Run as a single `jira_searchIssues` call with `maxResults: 200`.

Pipe the result through `extract-epic-issues.py`:

```bash
cat <<'EOF' | python3 ~/.claude/skills/epic-status/extract-epic-issues.py
<raw_jira_result>
EOF
```

This returns `{issues, pr_metadata_input, sprints}`. Unlike sprint-status, sub-tasks are included.

### Phase 4: Enrich with GitHub Metadata

If `pr_metadata_input` is non-empty, pipe it to `fetch-pr-metadata.py`:

```bash
echo '<pr_metadata_input_json>' | python3 ~/.claude/skills/.shared-scripts/fetch-pr-metadata.py
```

### Phase 5: Render Report

Assemble all data and pipe through `render-epic-report.py`. For the render input, use a heredoc since the assembled JSON is typically large:

```bash
cat <<'EOF' | python3 ~/.claude/skills/epic-status/render-epic-report.py
{"today":"2026-03-05","epic_key":"RHOAIENG-27992","epic_summary":"OCI Storage","my_username":"mikejturley","my_github":"mturley","issues":[...],"pr_metadata":[...]}
EOF
```

The input JSON format:
- `today`: today's date as `"YYYY-MM-DD"`
- `epic_key`: the selected epic key (e.g. `"RHOAIENG-27992"`)
- `epic_summary`: the shortened epic summary (e.g. `"OCI Storage"`)
- `my_username`: Jira username of the current user (e.g. `"mikejturley"`)
- `my_github`: GitHub username of the current user (e.g. `"mturley"`)
- `issues`: the `issues` array from Phase 3 (all epic issues with full field data)
- `pr_metadata`: the metadata array from Phase 4 (from `fetch-pr-metadata.py`), or `[]` if no PRs
- `show_closed`: (optional, default `false`) set to `true` to include Closed/Resolved issues in the output

Use `review_status_mine` from `fetch-pr-metadata.py` output for PRs on issues assigned to the current user, and `review_status_others` for all other PRs.

The report renders in two main sections:
- **My Assigned Issues**: A single table of active issues assigned to the current user, with Sprint and State columns
- **Other Epic Issues**: Grouped by status (Review → In Progress → Backlog), with Sprint and State columns

By default, Closed/Resolved issues are hidden. The report shows a summary line like _"4 Closed/Resolved issues hidden (13 story points). Say "show closed issues" to reveal them."_ after the My Assigned Issues table (if it had closed issues) and in place of the Closed/Resolved group.

If the user says "show closed issues" after the initial render, re-run `render-epic-report.py` with the same data but with `"show_closed": true` added to the input JSON. You do NOT need to re-fetch anything from Jira or GitHub — just re-render with the cached data.

**IMPORTANT:** Output the rendered report directly as text in the chat so the user can read it. Do NOT just leave the output in the tool result — the user cannot see tool results. Copy the full report output and send it as your response text.

The review status reference (for understanding the output):

| My Issues (`review_status_mine`) | Others' Issues (`review_status_others`) | Meaning |
|------|--------|---------|
| Draft | Draft | PR is a draft |
| Approved | Approved | Has `lgtm` + `approved` labels |
| Waiting for approval | Waiting for approval | Has `lgtm` but not `approved` |
| 🔴 **Has new comments** | Waiting for changes | Reviews exist, last review is after last commit |
| Waiting for re-review | 🔵 **Needs re-review** | Reviews exist, last commit is after last review |
| Waiting for review | 🟡 **Needs review** | No reviews at all |

## Important Notes

- Maximize parallel tool calls — run everything listed in each phase in a SINGLE tool-call round
- The report is read-only — do not modify any PRs or Jira issues
- **Never use inline Python** (`cat <<'PYEOF' | python3` with arbitrary code). All Bash commands must pipe to the skill helper scripts so they match the auto-approved permission patterns `echo *| python3 *epic-status/*`, `cat *| python3 *epic-status/*`, `echo *| python3 *sprint-status/*`, `cat *| python3 *sprint-status/*`, `echo *| python3 *.shared-scripts/*`, and `cat *| python3 *.shared-scripts/*`.
- For large JSON payloads that may exceed shell argument limits, use a heredoc piped to the script.
- When a Jira tool result is persisted to a file (output too large), read the file and include its content in the JSON payload — `extract-epic-issues.py` auto-detects the MCP wrapper format.
