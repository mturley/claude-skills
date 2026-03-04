# PR Dashboard

Generate a dashboard of open PRs I'm involved with, cross-referenced with RHOAIENG Jira issues.

**Technical Reference:** For Jira field IDs and formats, see [`../.mcp-usage/jira.md`](../.mcp-usage/jira.md)

## Instructions

### Phase 1: Gather PRs from GitHub

Run the following three searches in parallel using `gh search prs`:
- `--author=@me --state=open` (my PRs)
- `--reviewed-by=@me --state=open` (PRs I reviewed)
- `--commenter=@me --state=open` (PRs I commented on)

Request JSON fields: `repository,title,number,url,updatedAt,author`

**Filtering:**
- Exclude PRs updated over 1 year ago from the tables. Report the count of excluded PRs at the bottom.
- Deduplicate the reviewed/commented lists and remove any PRs authored by me from those lists (they belong in "My Open PRs").

### Phase 2: Gather PR metadata from GitHub

For each PR, fetch the following data in parallel using `gh api` and `gh pr checks`:

1. **PR info:** `gh api repos/{owner}/{repo}/pulls/{number}` — extract `labels` (array of names), `draft` (boolean), `mergeable_state`
2. **Reviews:** `gh api repos/{owner}/{repo}/pulls/{number}/reviews` — extract total count (`length`) and last review timestamp (`sort_by(.submitted_at) | last | .submitted_at`)
3. **Commits:** `gh api repos/{owner}/{repo}/pulls/{number}/commits` — extract last commit timestamp (`last | .commit.committer.date`)
4. **CI status:** `gh pr checks {number} --repo {owner/repo}` — determine overall status:
   - All SUCCESS → "Passed"
   - Any FAILURE → "Failed"
   - Any PENDING (and no failures) → "Running"
   - Otherwise → "N/A"

### Phase 3: Determine Review Status

**For My Open PRs** (action needed by me is **bold**):

| Status | Condition | Bold? |
|--------|-----------|-------|
| Draft | PR is a draft | No |
| Approved | Has `lgtm` AND `approved` labels | No |
| Waiting for approval | Has `lgtm` but not `approved` | No |
| **Needs changes** | Has reviews, last review is AFTER last commit, no `lgtm` label | **Yes** |
| Waiting for re-review | Has reviews, last commit is AFTER last review | No |
| Waiting for review | No reviews at all | No |

**For Others' PRs** (action needed by me is **bold**):

| Status | Condition | Bold? |
|--------|-----------|-------|
| Draft | PR is a draft | No |
| Approved | Has `lgtm` AND `approved` labels | No |
| Waiting for approval | Has `lgtm` but not `approved` | No |
| Waiting for changes | Has reviews, last review is AFTER last commit, no `lgtm` label | No |
| **Needs re-review** | Has reviews, last commit is AFTER last review, no `lgtm` label | **Yes** |
| **Needs review** | No reviews at all | **Yes** |

**Conflict suffix:** If `mergeable_state` is `dirty`, append ` **(conflicts)**` to the status.

Evaluate conditions top-to-bottom; use the first match.

### Phase 4: Cross-reference with Jira

For each PR, search RHOAIENG Jira for issues that reference the PR URL in the Git Pull Request field (`customfield_12310220`):

```
project = RHOAIENG AND cf[12310220] ~ "{partial_pr_path}"
```

Use a partial path like `kubeflow/model-registry/pull/2274` or `odh-dashboard/pull/6466` (strip the `https://github.com/` prefix and the org prefix for odh-dashboard).

Run all Jira searches in parallel.

For each matching Jira issue, extract:
- **Issue key** (e.g., RHOAIENG-51543)
- **Issue type** (Bug, Story, Task)
- **Status** (e.g., In Progress, Review, Closed)
- **Priority** (e.g., Blocker, Critical, Major, Normal, Minor)
- **Sprint** — parse from `customfield_12310940` string, extract the sprint name, shorten to just the number portion (e.g., "Dashboard - Green-35" → "Green-35")
- **Epic Link** — `customfield_12311140` (e.g., "RHOAIENG-27992")

### Phase 5: Resolve Epic Names

Collect all unique epic keys found in Phase 4. For each unique epic, fetch the issue using `jira_getIssue` and extract the summary. Shorten it to a concise label (e.g., "Dashboard - OCI Compliant Storage layer for Model Registry" → "OCI Storage").

Run epic lookups in parallel.

### Phase 6: Gather Sprint Review PRs

Find the current active Green sprint by searching for any RHOAIENG issue in an open sprint whose name contains "Green":

```
project = RHOAIENG AND sprint in openSprints() AND sprint = "Dashboard - Green-{N}" AND status = Review
```

Use the sprint name identified in Phase 4 data, or search for the active Green sprint.

For each issue found:
1. Extract the Git Pull Request field (`customfield_12310220`) — this contains PR URLs
2. For each GitHub PR URL, check if the PR is already included in Tables 1 or 2 — if so, skip it
3. Skip non-GitHub URLs (e.g., GitLab merge requests)
4. For remaining PR URLs, fetch the PR from GitHub and check if it is still open — skip closed PRs
5. Fetch the same metadata as Phase 2 (labels, draft, mergeable_state, reviews, commits, CI)
6. Determine review status using the "Others' PRs" rules from Phase 3
7. The Jira data is already available from the search results (issue key, type, status, priority, sprint, epic)

Resolve any new epic keys not already resolved in Phase 5.

### Phase 7: Render the Report

Sort all three tables by Jira priority (highest first: Blocker > Critical > Major > Normal > Minor) then by PR `updatedAt` descending (most recently updated first). PRs with no linked Jira issue sort after all prioritized PRs.

**Table 1: My Open PRs**

| PR | Title | Updated | Review Status | CI | Jira | Status | Priority | Sprint | Epic |
|----|-------|---------|---------------|-----|------|--------|----------|--------|------|

**Table 2: Open PRs I Reviewed or Commented On**

| PR | Author | Title | Updated | Review Status | CI | Jira | Status | Priority | Sprint | Epic |
|----|--------|-------|---------|---------------|-----|------|--------|----------|--------|------|

**Table 3: Other Open PRs from Green-{N} Issues in Review**

| PR | Author | Title | Updated | Review Status | CI | Jira | Status | Priority | Sprint | Epic |
|----|--------|-------|---------|---------------|-----|------|--------|----------|--------|------|

**Column formatting:**
- **PR**: `[repo-short#number](url)` — use short repo name (e.g., `model-registry`, `odh-dashboard`)
- **Title**: Truncate to 50 characters with ellipsis (e.g., "Add retry functionality for failed model transf...")
- **Updated**: Use relative dates — "today" for today, "Mon DD" for dates within the current year, "Mon YYYY" for older dates
- **Review Status**: Apply bold formatting per the rules in Phase 3
- **CI**: Passed, Failed, Running, or N/A
- **Jira**: `[RHOAIENG-XXXXX](url) (Type)` — link to `https://issues.redhat.com/browse/{key}`
- **Status**: Jira issue status (e.g., In Progress, Review, Closed)
- **Priority**: Jira issue priority (e.g., Blocker, Critical, Major, Normal, Minor)
- **Epic**: `[RHOAIENG-XXXXX](url) (Short Name)` — link to `https://issues.redhat.com/browse/{key}`
- Use `--` for empty cells

If a PR has multiple Jira issues, show additional rows with empty PR/Author/Title/Updated/Review Status/CI cells.

**Age filter note:** After Table 2, report the count of PRs excluded due to the 1-year age filter (this filter applies to the GitHub search results used by Tables 1 and 2).

## Important Notes

- Do NOT skip the Jira cross-reference or epic name lookup — these are key parts of the report
- Maximize parallel tool calls — GitHub API calls, Jira searches, and epic lookups should each be batched in parallel
- The report is read-only — do not modify any PRs or Jira issues
