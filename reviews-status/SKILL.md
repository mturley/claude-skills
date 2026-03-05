# Reviews Status

Show the review status of open PRs across my work, my team's sprint, and my scrum members, cross-referenced with RHOAIENG Jira issues.

**Technical Reference:** For Jira field IDs and formats, see [`../.mcp-usage/jira.md`](../.mcp-usage/jira.md)

**Helper Script:** `~/.claude/skills/reviews-status/fetch-pr-metadata.py` — fetches PR metadata in parallel via `gh api`. Pass a JSON array of `{owner, repo, number}` on stdin, get back a JSON array with `state`, `draft`, `labels`, `mergeable_state`, `review_count`, `last_review_at`, `last_commit_at`, `ci_status`.

**Helper Script:** `~/.claude/skills/reviews-status/extract-jira-fields.py` — parses Jira search results into compact JSON. Pass raw Jira response on stdin, get back `[{key, summary, type, status, priority, priority_sort, sprint, epic, pr_urls}]`. Supports `--filter-sprint Green` to filter by sprint name.

**Helper Script:** `~/.claude/skills/reviews-status/assign-tables.py` — deduplicates PRs and assigns them to tables. Two subcommands: `deduplicate` (after Phase 1) and `assign` (after Phase 2).

## Instructions

### Phase 1: Gather PRs and Context

Run ALL of the following in parallel in a single tool-call round:

1. `gh search prs --author=@me --state=open` with JSON fields `repository,title,number,url,updatedAt,author`
2. `gh search prs --reviewed-by=@me --state=open` with same JSON fields
3. `gh search prs --commenter=@me --state=open` with same JSON fields
4. Read `../.context/people.md` (for Table 4 team data). If missing, Table 4 will be skipped.

**Process PR lists:** Pipe the raw results through `assign-tables.py`:
```bash
echo '{"my_username":"...","max_age_days":365,"today":"YYYY-MM-DD","my_prs":<result1>,"reviewed_prs":<result2>,"commented_prs":<result3>}' | python3 ~/.claude/skills/reviews-status/assign-tables.py deduplicate
```

This outputs `table1_prs`, `table2_prs`, `excluded_count`, `all_prs` (for metadata fetch), and `jira_search_paths` (for Jira cross-reference).

If people.md was found, parse the **Green Scrum** section to extract GitHub usernames (skip the current user and blank entries).

### Phase 2: Metadata + Jira + Sprint Search + Team PRs

Run ALL of the following in parallel in a single tool-call round:

1. **Fetch metadata for Tables 1+2:** Pipe the `all_prs` array from `assign-tables.py deduplicate` to `fetch-pr-metadata.py`:
   ```bash
   echo '<all_prs_json>' | python3 ~/.claude/skills/reviews-status/fetch-pr-metadata.py
   ```

2. **Jira cross-reference for all PRs:** For each path in `jira_search_paths` from `assign-tables.py deduplicate`, search Jira:
   ```
   project = RHOAIENG AND cf[12310220] ~ "{partial_pr_path}"
   ```
   Run all Jira searches in parallel.

3. **Sprint review Jira search** (for Table 3): Search for issues in review in the current open sprint:
   ```
   project = RHOAIENG AND sprint in openSprints() AND component = "AI Core Dashboard" AND status = Review
   ```
   Pipe the result through `extract-jira-fields.py` to parse and filter:
   ```bash
   echo '<jira_result_json>' | python3 ~/.claude/skills/reviews-status/extract-jira-fields.py --filter-sprint Green
   ```
   This extracts compact fields and keeps only issues with "Green" in their sprint name.

4. **Team member PR searches** (for Table 4, skip if no people.md): For each Green Scrum member's GitHub username, run:
   ```bash
   gh search prs --author={username} --state=open --json repository,title,number,url,updatedAt,author
   ```

**After this round, extract from Jira results:**
For individual Jira cross-reference results, pipe each through `extract-jira-fields.py` or parse the compact fields directly (these are small enough to process inline). The sprint review results are already parsed by `extract-jira-fields.py` from step 3.

**Assign Table 3+4 candidates:** Pipe the collected data through `assign-tables.py`:
```bash
echo '{"my_username":"...","max_age_days":365,"today":"YYYY-MM-DD","table1_prs":<from_phase1>,"table2_prs":<from_phase1>,"sprint_review_issues":<from_extract_jira>,"team_prs":{"username1":<search_result>,...}}' | python3 ~/.claude/skills/reviews-status/assign-tables.py assign
```

This handles deduplication, age filtering, PR URL parsing, and outputs:
- `table3_candidates` — PRs from sprint review issues, each with their source `jira` data attached
- `table4_candidates` — team member PRs not in Tables 1-3
- `metadata_input` — combined Table 3+4 candidates formatted for `fetch-pr-metadata.py`
- `epic_keys` — unique epic keys for resolution
- `table4_jira_paths` — partial paths for Table 4 Jira link checks

Table 3 candidates have empty `title`, `author`, `updated_at` fields that will be filled by the metadata fetch in Phase 3.

### Phase 3: Remaining Metadata + Epics + Table 4 Jira Checks

Run ALL of the following in parallel in a single tool-call round:

1. **Fetch metadata for Table 3+4 candidates:** Pipe `metadata_input` from `assign-tables.py assign` to `fetch-pr-metadata.py`. After results return, drop any PRs with `state` != `"open"`.

2. **Resolve epic names:** For each key in `epic_keys` from `assign-tables.py assign`, fetch the issue using `jira_getIssue` and extract the summary. Shorten to a concise label (e.g., "Dashboard - OCI Compliant Storage layer for Model Registry" → "OCI Storage"). Run all lookups in parallel.

3. **Table 4 Jira link checks:** For each path in `table4_jira_paths` from `assign-tables.py assign`, search Jira using `project = RHOAIENG AND cf[12310220] ~ "{path}"`. Keep only Table 4 PRs with **NO** matching Jira issue. Run all searches in parallel.

After this round, resolve any new epic keys found in Table 3 Jira data that weren't already resolved.

### Phase 4: Render the Report

#### Review Status

The `fetch-pr-metadata.py` script computes review status automatically. Each PR in its output includes two pre-formatted fields:
- `review_status_mine` — use for Table 1 (my PRs)
- `review_status_others` — use for Tables 2, 3, and 4 (others' PRs)

These fields contain the final markdown string for the Review Status column, including bold formatting, emojis, and suffixes for conflicts/CI failures. Copy them directly into the table cell.

**Possible values** (bold = action needed by me):

| My PRs (`review_status_mine`) | Others' PRs (`review_status_others`) | Meaning |
|------|--------|---------|
| Draft | Draft | PR is a draft |
| Approved | Approved | Has `lgtm` + `approved` labels |
| Waiting for approval | Waiting for approval | Has `lgtm` but not `approved` |
| 🔴 **Has new comments** | Waiting for changes | Reviews exist, last review is after last commit |
| Waiting for re-review | 🔵 **Needs re-review** | Reviews exist, last commit is after last review |
| Waiting for review | 🟡 **Needs review** | No reviews at all |

#### Sorting

Sort Tables 1-3 by Jira priority (highest first: Blocker > Critical > Major > Normal > Minor) then by PR `updatedAt` descending. PRs with no linked Jira issue sort after all prioritized PRs. Sort Table 4 by `updatedAt` descending only.

#### Tables

Output a single markdown document with heading `# PR Dashboard` followed by these tables as level-2 headings:

## 1: My Open PRs

| PR | Title | Updated | Review Status | Jira | Priority | Status | Sprint | Epic |
|----|-------|---------|---------------|------|----------|--------|--------|------|

## 2: PRs I'm Reviewing

| PR | Author | Title | Updated | Review Status | Jira | Priority | Status | Sprint | Epic |
|----|--------|-------|---------|---------------|------|----------|--------|--------|------|

## 3: Other PRs for Green-{N} Issues in `Review`

_This table shows PRs linked to Green-{N} Jira issues that are in Review status, excluding those already listed above._

| PR | Author | Title | Updated | Review Status | Jira | Priority | Status | Sprint | Epic |
|----|--------|-------|---------|---------------|------|----------|--------|--------|------|

**IMPORTANT:** For this table, use the Jira mapping preserved in Phase 2 to populate the Jira, Priority, Status, Sprint, and Epic columns. Each PR in this table came from a specific Jira issue in Review status.

## 4: Other Green Scrum PRs with No Jira

| PR | Author | Title | Updated | Review Status |
|----|--------|-------|---------|---------------|

If people.md was not found, output after Table 3:
> _Table 4 (Other Green Scrum PRs with No Jira) was excluded because `.context/people.md` was not found. Run `/populate-people` to generate it._

#### Column Formatting

- **PR**: `[repo-short#number](url)` — use short repo name (e.g., `model-registry`, `odh-dashboard`)
- **Title**: Truncate to 50 characters with ellipsis
- **Updated**: Relative dates — "today" for today, "Mon DD" for current year, "Mon YYYY" for older
- **Review Status**: Apply bold formatting and emoji per the rules above, append conflict/CI status suffixes as needed
- **Jira**: `[RHOAIENG-XXXXX](url) (Type)` — link to `https://issues.redhat.com/browse/{key}`
- **Priority**: Jira issue priority (Critical, Major, Normal, Minor, etc.)
- **Status**: Jira issue status (In Progress, Review, etc.)
- **Sprint**: Shortened sprint name (e.g., "Green-35")
- **Epic**: `[RHOAIENG-XXXXX](url) (Short Name)` — link to `https://issues.redhat.com/browse/{key}`, use concise epic name
- Use `--` for empty cells

If a PR has multiple Jira issues, show additional rows with empty PR/Author/Title/Updated/Review Status cells.

**Age filter note:** After Table 2, report the count of PRs excluded due to the 1-year age filter.

#### Recommendations Section

After all tables, add a `## Recommended Actions` section. Analyze the dashboard data and provide prioritized recommendations for what to focus on first. Consider:
- PRs that are blocking (your PRs with new comments, especially with failed CI)
- High-priority items waiting for your review
- Items that would unblock team members
- Critical/Major priority Jira issues

Keep recommendations concise and actionable. Mention CI failures and conflicts in the recommendation text where relevant.

## Important Notes

- Do NOT skip the Jira cross-reference or epic name lookup — these are key parts of the report
- Maximize parallel tool calls — run everything listed in each phase in a SINGLE tool-call round
- The report is read-only — do not modify any PRs or Jira issues
