# Review Pull Request

Review a pull request in an isolated git worktree so multiple PRs can be reviewed simultaneously without affecting the main working tree.

## Arguments

- `$ARGUMENTS` - The PR number, branch name, or URL to review

## Workflow

### Phase 1: Pre-flight Checks

1. Verify the PR belongs to the current repository:
   - Get the current repo: `gh repo view --json nameWithOwner --jq '.nameWithOwner'`
   - Get the PR's base repo: If `$ARGUMENTS` is a URL (contains "github.com"), parse the owner/repo from the URL path. Otherwise, assume it's a local PR number/branch.
   - If they don't match, **abort** with a message explaining that the PR is from a different repository and cannot be checked out here
2. Get the PR number: `gh pr view $ARGUMENTS --json number --jq '.number'`
3. Check if a worktree for this PR already exists at `.claude/worktrees/pr-<number>`:
   - If it does, ask the user whether to reuse the existing worktree or remove and recreate it
   - To remove: `git worktree remove .claude/worktrees/pr-<number> --force`

### Phase 2: Create Worktree and Checkout PR Branch

1. Get the PR URL: `gh pr view $ARGUMENTS --json url --jq '.url'`
2. Extract the base repo from the URL (e.g. `https://github.com/org/repo/pull/123` → `org/repo`)
3. Fetch the PR ref into a local branch: `git fetch https://github.com/<base_repo>.git refs/pull/<number>/head:review/pr-<number>`
   - This works regardless of fork configuration since PR refs always exist on the base repository
4. Create the worktree: `git worktree add .claude/worktrees/pr-<number> review/pr-<number>`
5. If the worktree creation fails, report the error and abort
6. From this point forward, use the worktree path as the working directory when reading files for review. Run `gh` commands from the worktree directory.

### Phase 3: Gather PR Context

1. Get PR details: `gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`
2. Get the list of changed files: `gh pr diff $ARGUMENTS --name-only`
3. Get the full diff: `gh pr diff $ARGUMENTS`

### Phase 4: Check for Existing Reviews

1. Fetch existing review comments: `gh api repos/{owner}/{repo}/pulls/{pr_number}/comments`
2. Fetch existing PR reviews: `gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews`
3. If there are existing comments or review feedback:
   - List each unresolved comment/suggestion
   - For each comment, analyze the current diff to determine if it has been addressed
   - Provide a summary: "X of Y previous comments have been addressed"
   - For any unaddressed comments, explain what still needs to be done

### Phase 5: Review the PR

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

### Post-Review

After completing the review, tell the user:

1. **Where the worktree is**: `.claude/worktrees/pr-<number>` (provide the absolute path)
2. **How to open it in their editor**:
   - VS Code: `code .claude/worktrees/pr-<number>`
   - VS Code (new window): `code --new-window .claude/worktrees/pr-<number>`
   - Terminal: `cd .claude/worktrees/pr-<number>`
3. **How to clean up when done**:
   - `git worktree remove .claude/worktrees/pr-<number>`
   - Or to clean up all review worktrees: `git worktree list` then remove as needed
