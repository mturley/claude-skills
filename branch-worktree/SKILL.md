# Branch Worktree

Set up an isolated git worktree for a new branch and open it in a new editor window.

## Arguments

- `$ARGUMENTS` - The branch name to create

## Workflow

### Phase 1: Set Up Worktree

1. Confirm we're in a git repository: `git rev-parse --is-inside-work-tree 2>/dev/null`
   - If not, **abort** with a message asking the user to run the skill from a git repo
2. Get the repo name: `basename "$(git rev-parse --show-toplevel)"`
3. Parse the branch name from `$ARGUMENTS`:
   - Trim whitespace
   - If empty, **abort** with a message asking the user to provide a branch name
4. Generate the worktree directory name: `<repo-name>-<branch-name>` (e.g. `odh-dashboard-fix-login-validation`)
   - Replace any `/` in the branch name with `-` for the directory name
5. The git branch name is just `$ARGUMENTS` as provided (do NOT include the repo name in the branch)
6. Check if a worktree already exists at `.claude/worktrees/<worktree-name>`:
   - If it does, tell the user and ask whether to:
     - **Reuse**: just open the existing worktree in a new editor window
     - **Recreate**: remove and recreate the worktree from scratch (`git worktree remove <existing-path> --force`)
7. Create the worktree with a new branch: `git worktree add .claude/worktrees/<worktree-name> -b <branch-name>`
   - If the branch already exists (exit code non-zero), try without `-b`: `git worktree add .claude/worktrees/<worktree-name> <branch-name>`
   - If that also fails, report the error and abort

### Phase 2: Detect Editor and Open New Window

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

1. **Where the worktree is**: provide the absolute path to `.claude/worktrees/<worktree-name>`
2. **What branch was created**: the git branch name
3. **Dependencies not installed**: The worktree is a fresh checkout with no dependencies installed. If you need to build or test the code, you'll need to install dependencies first (e.g. `npm install`, `pip install`, `go mod download`, etc.) just like a fresh clone.
4. **How to clean up when done**: You can ask Claude to clean up the worktree for you, or do it manually:
   - `git worktree remove .claude/worktrees/<worktree-name>`
   - Or to list all worktrees: `git worktree list`
