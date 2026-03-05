# Review Pull Request

Review a pull request by checking out its branch and analyzing the changes.

## Arguments

- `$ARGUMENTS` - The PR number or branch name to review (passed to `gh pr checkout`)

## Workflow

### Phase 1: Pre-flight Checks

1. Run `git status` to check for uncommitted changes
2. If there are uncommitted changes, **abort** with a message asking the user to commit or stash their changes first
3. Verify the PR belongs to the current repository:
   - Get the current repo: `gh repo view --json nameWithOwner --jq '.nameWithOwner'`
   - Get the PR's base repo: If `$ARGUMENTS` is a URL (contains "github.com"), parse the owner/repo from the URL path. Otherwise, assume it's a local PR number/branch.
   - If they don't match, **abort** with a message explaining that the PR is from a different repository and cannot be checked out here

### Phase 2: Checkout PR Branch

1. Run `gh pr checkout $ARGUMENTS` to check out the PR branch
2. If this fails, report the error and abort

### Phase 3: Gather PR Context

1. Get PR details: `gh pr view --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles`
2. Get the list of changed files: `gh pr diff --name-only`
3. Get the full diff: `gh pr diff`

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

After completing the review, **remain on the PR branch**. Do not switch back to the original branch - the user may want to inspect the code further.
