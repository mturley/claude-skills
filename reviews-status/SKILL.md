# Reviews Status

Show the review status of open PRs across my work, my team's sprint, and my scrum members, cross-referenced with RHOAIENG Jira issues.

**Optional argument:** `exclude-jira` — skip all Jira lookups and render a faster report without Jira columns, Table 3, or epic data. When this argument is present, skip all `jira_searchIssues` calls and Jira-dependent processing in every phase.

**Technical Reference:** For Jira field IDs and formats, see [`../.context/jira-mcp.md`](../.context/jira-mcp.md)

**Helper Script:** `~/.claude/skills/reviews-status/gather-prs.py` — runs three `gh search prs` queries in parallel (--author, --reviewed-by, --commenter) and deduplicates results. Pass `{my_username, max_age_days, today}` on stdin, get back `{table1_prs, table2_prs, excluded_count, all_prs, jira_search_paths}`.

**Helper Script:** `~/.claude/skills/.shared-scripts/fetch-pr-metadata.py` — fetches PR metadata in parallel via `gh api`. Pass a JSON array of `{owner, repo, number}` on stdin, get back a JSON array with `state`, `draft`, `labels`, `mergeable_state`, `review_count`, `last_review_at`, `last_commit_at`, `ci_status`.

**Helper Script:** `~/.claude/skills/reviews-status/fetch-team-prs.py` — runs `gh search prs` for each team member in parallel. Pass `{usernames: [...]}` on stdin, get back `{username: [prs], ...}`.

**Helper Script:** `~/.claude/skills/reviews-status/assign-tables.py` — deduplicates PRs and assigns them to tables. Two subcommands: `deduplicate` (used internally by `gather-prs.py`) and `assign` (after Phase 2). The `assign` subcommand accepts raw Jira responses and handles extraction, cross-ref matching, and sprint filtering internally.

**Helper Script:** `~/.claude/skills/reviews-status/extract-jira-fields.py` — standalone Jira field parser (not called in the main flow; extraction is handled by `assign-tables.py assign`).

## Instructions

### Phase 1: Gather PRs and Context

Run ALL of the following in parallel in a single tool-call round:

1. Pipe `{"my_username":"...","max_age_days":365,"today":"YYYY-MM-DD"}` to `gather-prs.py`:
   ```bash
   echo '{"my_username":"...","max_age_days":365,"today":"YYYY-MM-DD"}' | python3 ~/.claude/skills/reviews-status/gather-prs.py
   ```
   This runs all three `gh search prs` queries internally and outputs `table1_prs`, `table2_prs`, `excluded_count`, `all_prs`, and `jira_search_paths`.

2. Read `../.context/people.md` (for Table 4 team data). If missing, Table 4 will be skipped.

3. **Discover the active Green sprint name** _(skip if `exclude-jira`)_: Run a Jira search to find any one issue in the current Green sprint:
   ```
   project = RHOAIENG AND sprint in openSprints() AND labels = "dashboard-green-scrum"
   ```
   Run as a single `jira_searchIssues` call with `maxResults: 1`.

After Phase 1 calls complete:

- _(skip if `exclude-jira`)_ Pipe the sprint discovery result through `extract-sprint-issues.py` to get the full sprint name:
  ```bash
  echo '<raw_jira_result>' | python3 ~/.claude/skills/sprint-status/extract-sprint-issues.py --filter-sprint Green
  ```
  Extract `sprint_full_name` from the output (e.g. `"Dashboard - Green-35"`).

If people.md was found, parse the **Green Scrum** section to extract GitHub usernames (skip the current user and blank entries).

### Phase 2: Metadata + Jira + Team PRs

Run ALL of the following in parallel in a single tool-call round:

1. **Fetch metadata for Tables 1+2:** Pipe the `all_prs` array from `gather-prs.py` to `fetch-pr-metadata.py`:
   ```bash
   echo '<all_prs_json>' | python3 ~/.claude/skills/.shared-scripts/fetch-pr-metadata.py
   ```

2. **Batched Jira cross-reference for all PRs** _(skip if `exclude-jira`)_: Construct a single JQL query using OR clauses for all paths in `jira_search_paths`:
   ```
   project = RHOAIENG AND (cf[12310220] ~ "path1" OR cf[12310220] ~ "path2" OR ...)
   ```
   Run this as a single `jira_searchIssues` call. The results will be matched to specific PRs by `assign-tables.py assign` via the `pr_urls` field.

3. **Sprint review Jira search** (for Table 3) _(skip if `exclude-jira`)_: Using the discovered `sprint_full_name`, search for issues in review in the current Green sprint:
   ```
   project = RHOAIENG AND sprint = "<sprint_full_name>" AND status = Review
   ```
   Run as a single `jira_searchIssues` call. Do NOT pipe through `extract-jira-fields.py` — the raw result goes directly to `assign-tables.py assign`.

4. **Team member PR searches** (for Table 4, skip if no people.md): Pipe the usernames to `fetch-team-prs.py`:
   ```bash
   echo '{"usernames":["user1","user2",...]}' | python3 ~/.claude/skills/reviews-status/fetch-team-prs.py
   ```

**Assign tables:** After all Phase 2 calls complete, pipe everything through `assign-tables.py assign`. Use a heredoc for large payloads:
```bash
cat <<'EOF' | python3 ~/.claude/skills/reviews-status/assign-tables.py assign
{"my_username":"...","max_age_days":365,"today":"YYYY-MM-DD","table1_prs":<from_phase1>,"table2_prs":<from_phase1>,"crossref_raw":<raw_jira_crossref_result>,"sprint_review_raw":<raw_jira_sprint_result>,"filter_sprint":"Green","team_prs":<from_fetch_team_prs>}
EOF
```

When `exclude-jira`, omit `crossref_raw` and `sprint_review_raw` from the input. The script handles missing keys gracefully — Table 1/2 PRs will have no `jira` arrays, Table 3 will be empty, and Table 4 will include all team PRs.

When a Jira tool result is persisted to a file (output too large for inline), pass the **file path as a string** for `crossref_raw` and/or `sprint_review_raw`. The script detects string values and reads the file automatically. Example: `"crossref_raw":"/path/to/tool-results/toolu_xxx.json"`. Do NOT attempt to read persisted files with the Read tool — they often exceed its token limit.

This handles Jira extraction, cross-ref matching to Table 1/2 PRs, sprint filtering, deduplication, age filtering, and PR URL parsing. It outputs:
- `table1_prs` — with `jira` arrays attached from cross-ref matching (empty when `exclude-jira`)
- `table2_prs` — with `jira` arrays attached from cross-ref matching (empty when `exclude-jira`)
- `table3_candidates` — PRs from sprint review issues, each with their source `jira` data attached (empty when `exclude-jira`)
- `table4_candidates` — team member PRs not in Tables 1-3
- `metadata_input` — combined Table 3+4 candidates formatted for `fetch-pr-metadata.py`
- `epic_keys` — unique epic keys for resolution
- `table4_jira_paths` — partial paths for Table 4 Jira link checks

Table 3 candidates have empty `title`, `author`, `updated_at` fields that will be filled by the metadata fetch in Phase 3.

### Phase 3: Remaining Metadata + Epics + Table 4 Jira Checks

Run ALL of the following in parallel in a single tool-call round:

1. **Fetch metadata for Table 3+4 candidates:** Pipe `metadata_input` from `assign-tables.py assign` to `fetch-pr-metadata.py`. After results return, drop any PRs with `state` != `"open"`. _(When `exclude-jira`, this is Table 4 candidates only since Table 3 is empty.)_

2. **Batched epic name lookup** _(skip if `exclude-jira`)_: If `epic_keys` is non-empty, construct a single JQL query:
   ```
   key in (RHOAIENG-27992, RHOAIENG-12345, ...)
   ```
   Run as a single `jira_searchIssues` call. Extract the summary from each issue and shorten to a concise label (e.g., "Dashboard - OCI Compliant Storage layer for Model Registry" → "OCI Storage").

3. **Batched Table 4 Jira link checks** _(skip if `exclude-jira`)_: If `table4_jira_paths` is non-empty, construct a single JQL query:
   ```
   project = RHOAIENG AND (cf[12310220] ~ "path1" OR cf[12310220] ~ "path2" OR ...)
   ```
   Run as a single `jira_searchIssues` call. Then keep only Table 4 PRs whose path has **NO** match in the results. _(When `exclude-jira`, keep all Table 4 PRs.)_

After this round, resolve any new epic keys found in Table 3 Jira data that weren't already resolved.

### Phase 4: Render the Report

Assemble the collected data into JSON and pipe through `render-report.py`. For the render input, use a heredoc since the assembled JSON is typically large:

```bash
cat <<'EOF' | python3 ~/.claude/skills/reviews-status/render-report.py
{"today":"2026-03-05","sprint_number":"35","excluded_count":5,...}
EOF
```

The input JSON format:
- `today`: today's date as `"YYYY-MM-DD"`
- `sprint_number`: current sprint number (e.g. `"35"`)
- `excluded_count`: count of PRs excluded by age filter
- `people_md_found`: boolean
- `exclude_jira`: boolean (optional, default false) — when true, renders tables without Jira columns, skips Table 3, and adjusts Table 4 description
- `epics`: `{"RHOAIENG-XXXXX": "Short Name", ...}` mapping of epic keys to concise names
- `table1`: array of PR objects (my open PRs)
- `table2`: array of PR objects (PRs I'm reviewing)
- `table3`: array of PR objects (other Green sprint review PRs) — empty when `exclude_jira`
- `table4`: array of PR objects (team PRs with no Jira, or all team PRs when `exclude_jira`)

Each PR object in tables 1-3:
```json
{"repo":"odh-dashboard","number":6466,"url":"...","title":"...","author":"mturley","updated_at":"2026-03-04T17:41:50Z","review_status":"...","jira":[{"key":"RHOAIENG-51543","type":"Bug","priority":"Critical","priority_sort":2,"status":"In Progress","sprint":"Green-35","epic":"RHOAIENG-27992"}]}
```

Table 4 PR objects omit the `jira` field.

Use `review_status_mine` from `fetch-pr-metadata.py` output for table1 PRs, and `review_status_others` for tables 2-4.

The script handles sorting, title truncation, date formatting, multi-Jira rows, column formatting, table descriptions (Tables 3 and 4 each have a summary line), and generates the `## Recommended Actions` section automatically. Recommended actions are sorted by Jira priority across all categories (your PRs, teammate reviews, sprint PRs), with category as a tiebreaker (your PRs first at the same priority). Items without Jira (untracked team work, non-Jira reviews) are listed at the end.

**IMPORTANT:** Output the rendered report directly as text in the chat so the user can read it. Do NOT just leave the output in the tool result — the user cannot see tool results. Copy the full report output and send it as your response text.

The review status reference (for understanding the output):

| My PRs (`review_status_mine`) | Others' PRs (`review_status_others`) | Meaning |
|------|--------|---------|
| Draft | Draft | PR is a draft |
| Approved | Approved | Has `lgtm` + `approved` labels |
| Waiting for approval | Waiting for approval | Has `lgtm` but not `approved` |
| 🔴 **Has new comments** | Waiting for changes | Reviews exist, last review is after last commit |
| Waiting for re-review | 🔵 **Needs re-review** | Reviews exist, last commit is after last review |
| Waiting for review | 🟡 **Needs review** | No reviews at all |

## Important Notes

- Do NOT skip the Jira cross-reference or epic name lookup — these are key parts of the report (unless `exclude-jira` is specified)
- Maximize parallel tool calls — run everything listed in each phase in a SINGLE tool-call round
- The report is read-only — do not modify any PRs or Jira issues
- **Never use inline Python** (`cat <<'PYEOF' | python3` with arbitrary code). All Bash commands must pipe to the skill helper scripts so they match the auto-approved permission patterns `echo *| python3 *reviews-status/*`, `cat *| python3 *reviews-status/*`, `echo *| python3 *sprint-status/*`, `cat *| python3 *sprint-status/*`, `echo *| python3 *.shared-scripts/*`, and `cat *| python3 *.shared-scripts/*`.
- For large JSON payloads that may exceed shell argument limits, use a heredoc piped to the script:
  ```bash
  cat <<'EOF' | python3 ~/.claude/skills/reviews-status/render-report.py
  {"today":"2026-03-05","sprint_number":"35",...}
  EOF
  ```
- When a Jira tool result is persisted to a file (output too large), pass the **file path as a string** for `crossref_raw` and/or `sprint_review_raw` in the `assign-tables.py assign` input. The script reads file paths automatically. Do NOT attempt to read persisted files with the Read tool.
