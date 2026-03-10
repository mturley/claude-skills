# /review

Reviews pull requests by checking out the branch and analyzing changes file-by-file.

## Installation

Place the skill at `~/.claude/skills/review/` (symlink or copy).

## Prerequisites

- Must be in a git repository
- The repository must have the GitHub CLI (`gh`) configured
- Working tree must be clean (no uncommitted changes)

## Usage

```
/review <PR number or branch name>
```

When run from a `/pr-worktree` worktree, the argument is optional — the PR number is inferred from the branch name.

The skill will:
1. Detect the PR from the branch name (if no argument given)
2. Check for uncommitted changes (aborts if any)
3. Verify the PR belongs to the current repository
4. Check out the PR branch using `gh pr checkout` (skipped if already on the branch)
4. Gather PR context (title, body, author, diff)
5. Check for existing review comments and whether they've been addressed
6. Provide a thorough code review

## Review Output

The review includes:
- **Summary**: What the PR does based on title, description, and changes
- **File-by-file analysis**: Code quality, potential bugs, security, performance
- **Previous comments status**: Which review comments have been addressed
- **CI status**: Failing checks with root cause analysis
- **Overall assessment**: Does implementation match the goal? Missing pieces?
- **Suggestions**: Concrete, actionable feedback with line numbers

Reviews use emojis for scannable emphasis: 🔴 critical/blockers, 🟡 warnings, 🟢 passing/positive, ⚠️ unaddressed comments, 📝 notes, 🔧 infra failures.

After the review, you remain on the PR branch to inspect the code further.
