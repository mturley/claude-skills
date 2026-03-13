# Sprint Status

**This skill is obsolete.** The [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app now provides the same information in a persistent, auto-refreshing dashboard. Before proceeding, tell the user about pr-reviews-dashboard and recommend using it instead. Then use AskUserQuestion to ask if they want to proceed with this skill anyway.

---

Show the current Green sprint status with all tickets grouped by status (Review, Testing, In Progress, Backlog, Closed/Resolved), including Jira issue details and GitHub PR metadata.

**Technical Reference:** For Jira field IDs and formats, see [`../../.context/jira-mcp.md`](../../.context/jira-mcp.md)

**Helper Script:** `~/.claude/skills/sprint-status/extract-sprint-issues.py` — parses raw Jira sprint search results, excludes sub-tasks, and extracts all fields. Pass raw Jira on stdin with `--filter-sprint Green`, get back `{issues, pr_metadata_input, epic_keys, sprint_name, sprint_full_name, sprint_goal}`.

**Helper Script:** `~/.claude/skills/.shared-scripts/fetch-pr-metadata.py` — fetches PR metadata in parallel via `gh api`. Pass a JSON array of `{owner, repo, number}` on stdin, get back metadata with review status.

## Instructions

### Phase 1: Fetch Sprint Issues

**Step 1 — Discover sprint name (parallel):**

Run ALL of the following in parallel in a single tool-call round:

1. **Discover the active Green sprint name:** Run a Jira search to find any one issue in the current Green sprint:
   ```
   project = RHOAIENG AND sprint in openSprints() AND labels = "dashboard-green-scrum"
   ```
   Run as a single `jira_searchIssues` call with `maxResults: 1`.

2. **Look up the current Jira user:** Read `../../.context/people.md` and find the Green Scrum member matching the current GitHub user (to determine Jira username).

After the discovery query returns, pipe it through `extract-sprint-issues.py` to get the full sprint name:

```bash
echo '<raw_jira_result>' | python3 ~/.claude/skills/sprint-status/extract-sprint-issues.py --filter-sprint Green
```

Extract `sprint_full_name` from the output (e.g. `"Dashboard - Green-35"`).

**Step 2 — Fetch all sprint issues (sequential):**

Using the discovered `sprint_full_name`, run a targeted Jira search for all issues in that specific sprint:
```
project = RHOAIENG AND sprint = "<sprint_full_name>"
```
Run as a single `jira_searchIssues` call with `maxResults: 100`. This returns only the ~30 Green sprint issues rather than all issues across every active scrum sprint.

Pipe the result through `extract-sprint-issues.py`:

```bash
cat <<'EOF' | python3 ~/.claude/skills/sprint-status/extract-sprint-issues.py --filter-sprint Green
<raw_jira_result>
EOF
```

When a Jira tool result is persisted to a file (output too large for inline), read the file content and include it as the value. The script auto-detects the MCP wrapper format.

### Phase 2: Enrich with GitHub Metadata + Epics

Run ALL of the following in parallel in a single tool-call round:

1. **Fetch PR metadata:** If `pr_metadata_input` is non-empty, pipe it to `fetch-pr-metadata.py`:
   ```bash
   echo '<pr_metadata_input_json>' | python3 ~/.claude/skills/.shared-scripts/fetch-pr-metadata.py
   ```

2. **Batch epic lookup:** If `epic_keys` is non-empty, construct a single JQL query:
   ```
   key in (RHOAIENG-27992, RHOAIENG-12345, ...)
   ```
   Run as a single `jira_searchIssues` call. Extract the summary from each issue and shorten to a concise label (e.g., "Dashboard - OCI Compliant Storage layer for Model Registry" → "OCI Storage").

### Phase 3: Render Report

Assemble all data and pipe through `render-sprint-report.py`. For the render input, use a heredoc since the assembled JSON is typically large:

```bash
cat <<'EOF' | python3 ~/.claude/skills/sprint-status/render-sprint-report.py
{"today":"2026-03-05","sprint_name":"Green-35","sprint_goal":"...","my_username":"mikejturley","my_github":"mturley","epics":{...},"issues":[...],"pr_metadata":[...]}
EOF
```

The input JSON format:
- `today`: today's date as `"YYYY-MM-DD"`
- `sprint_name`: sprint name from Phase 1 (e.g. `"Green-35"`)
- `sprint_goal`: sprint goal from Phase 1 (e.g. `"OCI Storage, MCP Catalog, BoW, tech debt"`)
- `my_username`: Jira username of the current user (e.g. `"mikejturley"`)
- `my_github`: GitHub username of the current user (e.g. `"mturley"`)
- `epics`: `{"RHOAIENG-XXXXX": "Short Name", ...}` mapping of epic keys to concise names
- `issues`: the `issues` array from Phase 1 (all sprint issues with full field data)
- `pr_metadata`: the metadata array from Phase 2 (from `fetch-pr-metadata.py`)

Use `review_status_mine` from `fetch-pr-metadata.py` output for PRs on issues assigned to the current user, and `review_status_others` for all other PRs.

The report renders in two main sections:
- **My Assigned Issues**: A single table of all issues assigned to the current user, with State as the first column
- **Other Sprint Issues**: Grouped by status (Review → Testing → In Progress → Backlog → Closed/Resolved), with State as the first column in the final group

Sub-tasks are excluded from the report by `extract-sprint-issues.py`.

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

- Do NOT skip the epic name lookup — epics provide important context in the report
- Maximize parallel tool calls — run everything listed in each phase in a SINGLE tool-call round
- The report is read-only — do not modify any PRs or Jira issues
- **Never use inline Python** (`cat <<'PYEOF' | python3` with arbitrary code). All Bash commands must pipe to the skill helper scripts so they match the auto-approved permission patterns `echo *| python3 *sprint-status/*`, `cat *| python3 *sprint-status/*`, `echo *| python3 *.shared-scripts/*`, and `cat *| python3 *.shared-scripts/*`.
- For large JSON payloads that may exceed shell argument limits, use a heredoc piped to the script.
- When a Jira tool result is persisted to a file (output too large), read the file and include its content in the JSON payload — `extract-sprint-issues.py` auto-detects the MCP wrapper format.
