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
5. Get the PR number and title: `gh pr view $ARGUMENTS --json number,title,url --jq '{number: .number, title: .title, url: .url}'`
6. Generate a short slug from the PR title:
   - Lowercase the title
   - Replace non-alphanumeric characters with hyphens
   - Collapse consecutive hyphens
   - Trim leading/trailing hyphens
   - Truncate to 40 characters (at a word boundary if possible)
   - The worktree name is `pr-<number>-<slug>` (e.g. `pr-123-fix-login-validation`)
7. Check if a worktree for this PR already exists at `.claude/worktrees/pr-<number>-*` (glob match on the PR number prefix):
   - If it does, check whether it's up to date with the PR's latest changes:
     1. Fetch the latest PR ref: `git fetch https://github.com/<base_repo>.git refs/pull/<number>/head`
     2. Compare `FETCH_HEAD` with the worktree's current HEAD: `git -C <existing-path> rev-parse HEAD`
     3. If they match, the worktree is up to date — tell the user and ask whether to reuse or recreate
     4. If they differ, tell the user the worktree is behind the PR's latest changes and ask whether to:
        - **Update**: hard reset the worktree to the latest PR state: fetch into the existing branch (`git fetch https://github.com/<base_repo>.git refs/pull/<number>/head:<branch-name>` with `--force`), then `git -C <existing-path> reset --hard <branch-name>`
        - **Recreate**: remove and recreate the worktree from scratch (`git worktree remove <existing-path> --force`)
        - **Reuse as-is**: keep the worktree in its current state (e.g. if the user has local changes they want to keep)
   - To remove (if recreating): `git worktree remove <existing-path> --force`

### Phase 2: Create Worktree and Checkout PR Branch

1. Extract the base repo from the PR URL (e.g. `https://github.com/org/repo/pull/123` → `org/repo`)
2. Fetch the PR ref into a local branch: `git fetch https://github.com/<base_repo>.git refs/pull/<number>/head:review/pr-<number>-<slug>`
   - This works regardless of fork configuration since PR refs always exist on the base repository
3. Create the worktree: `git worktree add .claude/worktrees/pr-<number>-<slug> review/pr-<number>-<slug>`
4. If the worktree creation fails, report the error and abort

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

### Phase 4: Offer to Install Dependencies

Investigate the worktree to determine how to install dependencies, then offer to do it for the user.

#### Step 1: Investigate

Check the following in the worktree root, in order of priority:

1. **Documentation files** (`README.md`, `README.rst`, `README.txt`, `README`, `CONTRIBUTING.md`, `DEVELOPING.md`, `DEVELOPMENT.md`, `SETUP.md`): Scan for setup/installation sections (look for headings like "Getting Started", "Installation", "Setup", "Development", "Prerequisites", "Building"). Extract the recommended install commands.
2. **Makefile / makefile**: Look for common targets like `install`, `setup`, `deps`, `dependencies`, `init`, `bootstrap`. Read the target recipes to understand what they do.
3. **Lockfiles and manifest files** (fallback if READMEs/Makefiles don't have clear guidance):
   - `package-lock.json` → `npm ci`
   - `yarn.lock` → `yarn install`
   - `pnpm-lock.yaml` → `pnpm install`
   - `package.json` (no lockfile) → `npm install`
   - `requirements.txt` → `pip install -r requirements.txt`
   - `Pipfile.lock` → `pipenv install`
   - `poetry.lock` → `poetry install`
   - `pyproject.toml` (no lockfile) → `pip install -e .`
   - `go.mod` → `go mod download`
   - `Gemfile.lock` → `bundle install`
   - `Cargo.lock` → `cargo fetch`
   - `composer.lock` → `composer install`

If none of these are found, skip this phase entirely.

#### Step 2: Propose and confirm

Tell the user what you found (e.g. "The README says to run `make install`, which runs `npm ci` and builds the project") and what command(s) you would run. Ask whether they want you to install dependencies now.

#### Step 3: Install

If the user approves, run the install command(s) in the worktree directory and report success or failure.

### Post-Setup

After opening the editor window (or providing the path), tell the user:

1. **Where the worktree is**: provide the absolute path to `.claude/worktrees/pr-<number>-<slug>`
2. **Dependencies**: whether they were installed, or a reminder to install them if the user declined or no dependency manager was detected
3. **What to do next**: "Run `/review` in the new window to start the code review"
4. **How to clean up when done**: You can ask Claude to clean up the worktree for you, or do it manually:
   - `git worktree remove .claude/worktrees/pr-<number>-<slug>`
   - Or to clean up all review worktrees: `git worktree list` then remove as needed
