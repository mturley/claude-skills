# Branch Worktree

Set up an isolated git worktree for a new branch and open it in a new editor window.

## Arguments

- `$ARGUMENTS` - The branch name to create

## Execution

Run the script and report its output to the user:

```bash
"$(readlink -f ~/.claude/skills)/branch-worktree/branch-worktree.sh" $ARGUMENTS
```

The script handles everything interactively: worktree creation, gitignored file copying, editor detection, and dependency detection. It prompts the user directly for any choices needed.
