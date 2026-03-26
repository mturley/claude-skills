# PR Worktree

Set up an isolated git worktree for a pull request and open it in a new editor window for review.

## Arguments

- `$ARGUMENTS` - The PR number, branch name, or URL

## Execution

Run the script and report its output to the user:

```bash
"$(readlink -f ~/.claude/skills)/pr-worktree/pr-worktree.sh" $ARGUMENTS
```

The script handles everything interactively: worktree creation, gitignored file copying, editor detection, and dependency detection. It prompts the user directly for any choices needed.
