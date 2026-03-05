# /pr-worktree

Creates an isolated git worktree for a pull request and opens it in a new editor window. Designed to be used with `/review` -- set up the worktree first with `/pr-worktree`, then run `/review` in the new window.

## Installation

Place the skill at `~/.claude/skills/pr-worktree/` (symlink or copy).

## Prerequisites

- The GitHub CLI (`gh`) must be configured
- If using a PR number or branch name, must be in the correct git repository
- If using a full PR URL, the skill can find a local clone automatically (searches `~/`)

## Usage

```
/pr-worktree <PR number, branch name, or URL>
```

The skill will:
1. Find or verify the correct local repository (searches `~/` if needed)
2. Create a git worktree at `.claude/worktrees/pr-<number>-<slug>` (or reuse/update an existing one)
3. Check out the PR branch in the worktree
4. Detect your editor (VS Code, Cursor, or terminal)
5. Open a new editor window in the worktree directory
6. Tell you to run `/review` in the new window

If a worktree for the PR already exists, the skill fetches the latest PR ref and compares it to the worktree's HEAD. If the worktree is behind, it offers to update (hard reset), recreate from scratch, or reuse as-is.

## Editor Detection

The skill automatically detects your editor environment:
- **VS Code**: Opens with `code --new-window`
- **Cursor**: Opens with `cursor --new-window`
- **Terminal**: Provides the worktree path and offers to open an editor for you

## Cleanup

```bash
# Remove a specific review worktree
git worktree remove .claude/worktrees/pr-<number>-<slug>

# List all worktrees
git worktree list
```
