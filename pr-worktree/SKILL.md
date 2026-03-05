# PR Worktree

Set up an isolated git worktree for a pull request and open it in a new editor window for review.

## Arguments

- `$ARGUMENTS` - The PR number, branch name, or URL

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

### Phase 3: Detect Editor and Open New Window

Detect the user's editor environment and open a new window in the worktree directory.

**Detection logic** (check Cursor before VS Code, since Cursor is a VS Code fork and may also set `VSCODE_*` variables):

1. **Cursor**: Check if `CURSOR_CHANNEL` env var is set, or if `__CFBundleIdentifier` contains "cursor"
   - Open with: `cursor --new-window <worktree-path>`
2. **VS Code**: Check if `VSCODE_PID` env var is set, or if `TERM_PROGRAM` is "vscode"
   - Open with: `code --new-window <worktree-path>`
3. **Terminal (no editor detected)**: Print the worktree path and example commands for common editors, then ask the user if they want Claude to open an editor for them:
   - `code --new-window <worktree-path>`
   - `cursor --new-window <worktree-path>`
   - `cd <worktree-path>`

### Post-Setup

After opening the editor window (or providing the path), tell the user:

1. **Where the worktree is**: provide the absolute path to `.claude/worktrees/pr-<number>`
2. **What to do next**: "Run `/review <PR-number>` in the new window to start the code review"
3. **How to clean up when done**:
   - `git worktree remove .claude/worktrees/pr-<number>`
   - Or to clean up all review worktrees: `git worktree list` then remove as needed
