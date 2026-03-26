# /branch-worktree (Obsolete)

> **This skill has been replaced by the standalone `branch-worktree` CLI command in [mturley/work-scripts](https://github.com/mturley/work-scripts).** Install it via PATH and run `branch-worktree <name>` directly from your terminal.

Creates an isolated git worktree for a new branch and opens it in a new editor window. Useful for starting work on a new feature or fix without affecting your current working tree.

## Installation

Place the skill at `~/.claude/skills/branch-worktree/` (symlink or copy).

## Usage

```
/branch-worktree <branch-name>
```

The skill will:
1. Create a git worktree at `.claude/worktrees/<repo-name>-<branch-name>` with a new branch
2. Detect your editor (VS Code, Cursor, or terminal)
3. Open a new editor window in the worktree directory
4. Offer to copy gitignored files (e.g. `node_modules/`, build artifacts) from the main working tree so the worktree is ready to use immediately

If a worktree with that name already exists, the skill offers to reuse it or recreate it.

## Editor Detection

The skill automatically detects your editor environment:
- **VS Code**: Opens with `code --new-window`
- **Cursor**: Opens with `cursor --new-window`
- **Terminal**: Provides the worktree path and offers to open an editor for you

## Cleanup

```bash
# Remove a specific worktree
git worktree remove .claude/worktrees/<repo-name>-<branch-name>

# List all worktrees
git worktree list
```
