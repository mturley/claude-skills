---
name: review
description: Review a pull request by checking out its branch and analyzing the changes
---

# Review Pull Request

Review a pull request by checking out its branch and analyzing the changes.

## Arguments

- `$ARGUMENTS` - The PR number or branch name to review (passed to `gh pr checkout`). Optional when run from a `/pr-worktree` worktree — the PR number is inferred from the branch name.

## Workflow

### Phase 1: Pre-flight Checks

1. If `$ARGUMENTS` is empty, check the current branch: `git branch --show-current`
   - If the branch matches the pattern `review/pr-<number>-*` (e.g. `review/pr-123-fix-login`), extract the PR number and use it as `$ARGUMENTS`. Note that the checkout in Phase 2 should be skipped since we're already on the correct branch.
   - If it doesn't match, **abort** with a message explaining that a PR number or branch name is required
2. Verify the PR belongs to the current repository:
   - Get the current repo: `gh repo view --json nameWithOwner --jq '.nameWithOwner'`
   - Get the PR's base repo: If `$ARGUMENTS` is a URL (contains "github.com"), parse the owner/repo from the URL path. Otherwise, assume it's a local PR number/branch.
   - If they don't match, **abort** with a message explaining that the PR is from a different repository and cannot be checked out here
3. **STOP AND ASK before creating a worktree.** Check whether the working tree is clean and on `main`:
   - Run `git branch --show-current` and `git status --short`
   - If already on `main` with no changes, proceed directly to Phase 2 — no worktree needed.
   - Otherwise (not on `main`, or uncommitted changes exist), **you MUST ask the user before proceeding**. Do NOT create a worktree or check out the PR without explicit confirmation. Use `AskUserQuestion` to ask something like: "You're on branch X (with uncommitted changes). I recommend running `/pr-worktree <PR>` to set up an isolated worktree with dependencies copied over, then running `/review` in the new window. Or you can switch to main first. Which do you prefer?"
   - If the user chooses a worktree, run the `/pr-worktree` skill (which handles worktree creation, editor opening, and dependency copying). After `/pr-worktree` completes, tell the user to run `/review` in the new editor window and stop — do not continue to Phase 2 in this session.
   - If the user declines, **abort** with a message suggesting they commit or stash their changes first, or switch to main manually.
   - **Exception:** If the user explicitly asked to use a worktree in their original message, proceed directly to run `/pr-worktree` without asking.

### Phase 2: Checkout PR Branch

1. If the PR number was inferred from the branch name in Phase 1, skip this phase — we're already on the correct branch
2. Run `gh pr checkout $ARGUMENTS` to check out the PR branch
3. If this fails, report the error and abort

### Phase 3: Gather PR Context

1. Get PR details: `gh pr view --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`
2. Get the list of changed files: `gh pr diff --name-only`
3. Get the full diff: `gh pr diff`

### Phase 4: Gather Jira Context

Look for related Jira issues to understand the requirements and acceptance criteria behind the PR.

**Read `~/.claude/skills/.context/jira-mcp.md`** before making any Jira MCP calls — it contains the cloudId, custom field IDs, and JQL patterns needed below.

#### Step 1: Search the PR description for Jira links

Scan the PR body (from Phase 3) for URLs matching `redhat.atlassian.net/browse/`. Extract any issue keys (e.g. `RHOAIENG-12345`).

#### Step 2: If no Jira links found, search by PR author

This handles upstream PRs or PRs that don't reference Jira directly.

1. Get the PR author's GitHub username (from Phase 3's `author` field)
2. Read `~/.claude/skills/.context/people.md` and find the row matching that GitHub username
3. If found, extract their Jira `accountId`
4. Search for open Jira issues assigned to that person that link to this PR. Use `searchJiraIssuesUsingJql` with:
   - JQL: `project = RHOAIENG AND assignee = "<accountId>" AND status != Done AND "Git Pull Request" ~ "<owner>/<repo>/pull/<pr_number>"` (extract owner/repo from the repository, pr_number from the PR)
   - `fields`: `["summary", "status", "customfield_10875"]`
5. If the PR-link search returns no results, broaden: search for issues assigned to that person in active sprints:
   - JQL: `project = RHOAIENG AND assignee = "<accountId>" AND sprint in openSprints() ORDER BY updated DESC`
   - Review the results and look for issues whose title/description appears related to the PR's changes
6. If no match is found by any method, skip this phase — not all PRs have Jira issues

#### Step 3: Fetch Jira issue details

For each Jira issue found (from either step), use `getJiraIssue` with `responseContentFormat: "markdown"` to get the full description, acceptance criteria, and status.

#### Step 4: Include Jira context in the review

When writing the review in Phase 7:
- Reference the Jira issue(s) with links
- Check the PR's changes against any acceptance criteria listed in the Jira description
- Note any open questions or scope items from the Jira issue that are relevant to the review
- If acceptance criteria exist, include a checklist showing which are met by the PR

### Phase 5: Check for Existing Reviews

1. Fetch existing review comments: `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments`
2. Fetch existing PR reviews: `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews`
3. If there are existing comments or review feedback:
   - List each unresolved comment/suggestion
   - For each comment, analyze the current diff to determine if it has been addressed
   - Provide a summary: "X of Y previous comments have been addressed"
   - For any unaddressed comments, explain what still needs to be done

### Phase 6: Check CI Status

1. Run `gh pr checks {pr_number}` to get the status of all CI checks
2. If any checks have failed:
   - For each failed check, fetch the failure logs: `gh run view {run_id} --log-failed` (extract the run ID from the check URL)
   - Analyze the logs to determine the root cause of each failure
   - Categorize failures: Is this caused by changes in this PR, or a pre-existing/infrastructure issue?
3. Include a **CI Status** section in the review output:
   - List all failing checks with their names and root causes
   - For PR-caused failures, provide specific guidance on how to fix them (e.g. lint errors, test failures, type errors)
   - For pre-existing/infrastructure failures, note that they appear unrelated to the PR changes

### Phase 7: Review the PR

Analyze the changes and provide a thorough code review:

1. **Summary**: Briefly describe what the PR does based on the title, description, and changes
2. **File-by-file analysis**: For each changed file, review:
   - What changed and why (based on context)
   - Code quality concerns (readability, maintainability)
   - Potential bugs or edge cases
   - Security considerations
   - Performance implications
3. **Overall assessment**:
   - Does the implementation match the stated goal?
   - Are there any missing pieces (tests, documentation, etc.)?
   - Any architectural concerns?
4. **Suggestions**: Concrete, actionable feedback for improvement

Be constructive and specific. Reference line numbers when pointing out issues.

Use emojis for emphasis throughout the review to make important information scannable:
- 🔴 for critical issues, CI failures caused by the PR, and blockers
- 🟡 for warnings, medium-severity concerns, and things that should be addressed
- 🟢 for passing checks, addressed comments, and positive observations
- ⚠️ for unaddressed review comments and remaining action items
- 📝 for informational notes and suggestions
- 🔧 for pre-existing/infrastructure CI failures unrelated to the PR

### Post-Review (after Phase 7)

After completing the review:

1. **Remain on the PR branch**. Do not switch back to the original branch - the user may want to inspect the code further.
2. **End your output with a link to the PR**: Get the PR URL from `gh pr view --json url --jq '.url'` and display it as a clickable markdown link at the very end of your review.
