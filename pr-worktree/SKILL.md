# PR Worktree

Set up an isolated git worktree for a pull request and open it in a new editor window for review.

## Arguments

- `$ARGUMENTS` - The PR number, branch name, or URL

## Workflow

### Phase 1: Find or Verify Repository

1. Determine the target repo from `$ARGUMENTS`:
   - If `$ARGUMENTS` is a URL (contains "github.com"), parse the `owner/repo` from the URL path
   - Otherwise, assume it's a local PR number/branch for the current repo
2. Check if we're in the right git repository:
   - Run `git rev-parse --is-inside-work-tree 2>/dev/null` to check if we're in a git repo at all
   - If in a git repo, run `gh repo view --json nameWithOwner --jq '.nameWithOwner'` and compare to the target repo
3. If **not in a git repo** or **in the wrong repo**, and the target repo was identified from a URL:
   - Search for a local clone under `~/` by looking for directories named after the repo:
     ```bash
     find ~/ -maxdepth 4 -type d -name "<repo-name>" -not -path "*/node_modules/*" -not -path "*/.claude/worktrees/*" 2>/dev/null
     ```
   - For each candidate, check if it's a git repo with a matching remote:
     ```bash
     git -C <candidate> remote -v 2>/dev/null | grep -q "<owner>/<repo-name>"
     ```
   - Use the first match and `cd` there for all subsequent commands
   - If no match is found, **abort** with a message explaining that no local clone was found
4. If not in a git repo and `$ARGUMENTS` is not a URL (not enough context to find the repo), **abort** with a message asking the user to run the skill from a git repo or provide a full PR URL
5. Get the PR number: `gh pr view $ARGUMENTS --json number --jq '.number'`
6. Check if a worktree for this PR already exists at `.claude/worktrees/pr-<number>`:
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

**Important**: When running inside a Claude Code session, use `env -u CLAUDECODE` when launching the editor so the new window doesn't inherit the session. Without this, Claude Code in the new window will refuse to start with a "nested session" error. This is harmless when `CLAUDECODE` is not set (e.g. when running from Cursor's AI), so always include it.

**Detection logic** (check Cursor before VS Code, since Cursor is a VS Code fork and may also set `VSCODE_*` variables):

1. **Cursor**: Check if `CURSOR_CHANNEL` env var is set, or if `__CFBundleIdentifier` contains "cursor"
   - Open with: `env -u CLAUDECODE cursor --new-window <worktree-path>`
2. **VS Code**: Check if `VSCODE_PID` env var is set, or if `TERM_PROGRAM` is "vscode"
   - Open with: `env -u CLAUDECODE code --new-window <worktree-path>`
3. **Terminal (no editor detected)**: Print the worktree path and example commands for common editors, then ask the user if they want Claude to open an editor for them:
   - `env -u CLAUDECODE code --new-window <worktree-path>`
   - `env -u CLAUDECODE cursor --new-window <worktree-path>`
   - `cd <worktree-path>`

### Post-Setup

After opening the editor window (or providing the path), tell the user:

1. **Where the worktree is**: provide the absolute path to `.claude/worktrees/pr-<number>`
2. **Dependencies not installed**: The worktree is a fresh checkout with no dependencies installed. If you need to build or test the code, you'll need to install dependencies first (e.g. `npm install`, `pip install`, `go mod download`, etc.) just like a fresh clone.
3. **What to do next**: "Run `/review` in the new window to start the code review"
4. **How to clean up when done**: You can ask Claude to clean up the worktree for you, or do it manually:
   - `git worktree remove .claude/worktrees/pr-<number>`
   - Or to clean up all review worktrees: `git worktree list` then remove as needed
