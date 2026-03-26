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
7. Run the shared worktree-ensure script to check/create the worktree in a single step:
   ```bash
   SCRIPTS_DIR="$(dirname "$(readlink -f ~/.claude/skills)")"/.shared-scripts
   "$SCRIPTS_DIR/worktree-ensure.sh" pr .claude/worktrees/pr-<number>-<slug> <number> <slug> <base_repo>
   ```
   - If status is `"exists"`: the worktree is up to date — tell the user and ask whether to reuse or recreate
   - If status is `"exists-outdated"`: tell the user the worktree is behind the PR's latest changes (show local_head vs remote_head) and ask whether to:
     - **Update**: hard reset the worktree to the latest PR state: fetch into the existing branch (`git fetch https://github.com/<base_repo>.git refs/pull/<number>/head:<branch-name>` with `--force`), then `git -C <existing-path> reset --hard <branch-name>`
     - **Recreate**: remove and recreate the worktree from scratch (`git worktree remove <existing-path> --force`), then re-run the script
     - **Reuse as-is**: keep the worktree in its current state (e.g. if the user has local changes they want to keep)
   - If status is `"created"`: proceed to Phase 2
   - If status is `"error"`: report the error and abort

### Phase 2: Copy Gitignored Files

Offer to copy gitignored files (installed dependencies, build artifacts, etc.) from the main working tree to the new worktree so it's ready to use immediately without reinstalling.

1. Get the main working tree root (the directory where the `git worktree add` command was run, not the worktree itself)
2. Run the shared gitignored-sizes script to list gitignored entries with their sizes:
   ```bash
   SCRIPTS_DIR="$(dirname "$(readlink -f ~/.claude/skills)")"/.shared-scripts
   "$SCRIPTS_DIR/gitignored-sizes.sh" <main-tree-root>
   ```
   - If no output, skip this phase silently and proceed to Phase 3
   - Otherwise, show the user the output (list of entries with sizes and total) and ask if they want to copy these to the worktree
3. If the user agrees, run the shared copy-gitignored script:
   ```bash
   "$SCRIPTS_DIR/copy-gitignored.sh" <main-tree-root> <worktree-path>
   ```
4. Report what was copied based on the script output and note any errors

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

### Phase 4: Determine How to Install Dependencies

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

1. **Where the worktree is**: provide the absolute path to `.claude/worktrees/pr-<number>-<slug>`
2. **Dependencies**:
   - If gitignored files were copied in Phase 2: note that dependencies and other gitignored files have been copied from the main working tree. Mention that if the PR changes dependencies (e.g. modified `package.json`), they may still need to run the install command to pick up differences.
   - If gitignored files were not copied (none found or user declined): Based on what you found in Phase 4, tell the user what to run. Provide copy-pasteable commands starting with `cd <absolute-worktree-path>`, followed by the install command(s). If you found instructions in a README or CONTRIBUTING guide, briefly mention where you found them. If nothing was found, just note that no dependency manager was detected.
3. **What to do next**: "Run `/review` in the new window to start the code review"
4. **How to clean up when done**: You can ask Claude to clean up the worktree for you, or do it manually:
   - `git worktree remove .claude/worktrees/pr-<number>-<slug>`
   - Or to clean up all review worktrees: `git worktree list` then remove as needed
