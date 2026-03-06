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

### Phase 3: Determine How to Install Dependencies

Investigate the worktree to figure out how to install dependencies, so you can tell the user.

Check the following in the worktree root, in order of priority:

1. **Documentation files** (`README.md`, `README.rst`, `README.txt`, `README`, `CONTRIBUTING.md`, `DEVELOPING.md`, `DEVELOPMENT.md`, `SETUP.md`): Scan for setup/installation sections (look for headings like "Getting Started", "Installation", "Setup", "Development", "Prerequisites", "Building"). Extract the recommended install commands.
2. **Makefile / makefile**: Look for common targets like `install`, `setup`, `deps`, `dependencies`, `init`, `bootstrap`. Read the target recipes to understand what they do.
3. **Lockfiles and manifest files** (fallback if docs/Makefiles don't have clear guidance):
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

### Post-Setup

After opening the editor window (or providing the path), tell the user:

1. **Where the worktree is**: provide the absolute path to `.claude/worktrees/<worktree-name>`
2. **What branch was created**: the git branch name
3. **How to install dependencies**: Based on what you found in Phase 3, tell the user what to run in their terminal. Provide copy-pasteable commands starting with `cd <absolute-worktree-path>`, followed by the install command(s). For example:
   ```
   cd /path/to/.claude/worktrees/<worktree-name>
   npm ci
   ```
   If you found instructions in a README or CONTRIBUTING guide, briefly mention where you found them (e.g. "Per the CONTRIBUTING.md, run `make install`"). If nothing was found, just note that no dependency manager was detected.
4. **How to clean up when done**: You can ask Claude to clean up the worktree for you, or do it manually:
   - `git worktree remove .claude/worktrees/<worktree-name>`
   - Or to list all worktrees: `git worktree list`
