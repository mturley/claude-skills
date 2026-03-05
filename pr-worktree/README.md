# /pr-worktree

Creates an isolated git worktree for a pull request and opens it in a new editor window. Designed to be used with `/review` -- set up the worktree first with `/pr-worktree`, then run `/review` in the new window.

## Installation

Place the skill at `~/.claude/skills/pr-worktree/` (symlink or copy).

## Prerequisites

- Must be in a git repository
- The repository must have the GitHub CLI (`gh`) configured

## Usage

```
/pr-worktree <PR number, branch name, or URL>
```

The skill will:
1. Verify the PR belongs to the current repository
2. Create a git worktree at `.claude/worktrees/pr-<number>`
3. Check out the PR branch in the worktree
4. Detect your editor (VS Code, Cursor, or terminal)
5. Open a new editor window in the worktree directory
6. Tell you to run `/review` in the new window

## Editor Detection

The skill automatically detects your editor environment:
- **VS Code**: Opens with `code --new-window`
- **Cursor**: Opens with `cursor --new-window`
- **Terminal**: Provides the worktree path and offers to open an editor for you

## Cleanup

```bash
# Remove a specific review worktree
git worktree remove .claude/worktrees/pr-<number>

# List all worktrees
git worktree list
```
