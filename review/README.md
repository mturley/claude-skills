# /review

Reviews pull requests in an isolated git worktree, allowing multiple PRs to be reviewed simultaneously without affecting your working tree.

## Installation

Place the skill at `~/.claude/skills/review/` (symlink or copy).

## Prerequisites

- Must be in a git repository
- The repository must have the GitHub CLI (`gh`) configured

## Usage

```
/review <PR number, branch name, or URL>
```

The skill will:
1. Verify the PR belongs to the current repository
2. Create a git worktree at `.claude/worktrees/pr-<number>`
3. Check out the PR branch in the worktree
4. Gather PR context (title, body, author, diff)
5. Check for existing review comments and whether they've been addressed
6. Provide a thorough code review

## Review Output

The review includes:
- **Summary**: What the PR does based on title, description, and changes
- **File-by-file analysis**: Code quality, potential bugs, security, performance
- **Previous comments status**: Which review comments have been addressed
- **Overall assessment**: Does implementation match the goal? Missing pieces?
- **Suggestions**: Concrete, actionable feedback with line numbers

## After the Review

The PR code remains available in the worktree. To inspect it yourself:

```bash
# Open in VS Code
code .claude/worktrees/pr-<number>

# Or in a new VS Code window
code --new-window .claude/worktrees/pr-<number>

# Or navigate in terminal
cd .claude/worktrees/pr-<number>
```

Multiple reviews can run in parallel since each PR gets its own worktree.

## Cleanup

```bash
# Remove a specific review worktree
git worktree remove .claude/worktrees/pr-<number>

# List all worktrees
git worktree list
```
