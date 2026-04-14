---
name: work
description: Start working on a Jira issue by gathering context and beginning implementation
disable-model-invocation: true
---

# Work on Jira Issue

Start working on a Jira issue by identifying the issue, validating the workspace, gathering context, and beginning implementation.

## Arguments

- `$ARGUMENTS` - Optional. A Jira issue key (e.g. `RHOAIENG-12345`), a Jira URL, or a keyword hint. If omitted, the skill will try to detect the issue from the current branch name or conversation history.

## Workflow

### Phase 1: Identify the Jira Issue

Determine the Jira issue key using the following sources, in priority order:

1. **From `$ARGUMENTS`**: If provided, extract the issue key.
   - If it's a full URL (`redhat.atlassian.net/browse/RHOAIENG-12345`), extract the key.
   - If it's an issue key (e.g. `RHOAIENG-12345`), use it directly.
2. **From the current branch name**: Run `git branch --show-current` and look for a Jira issue key pattern (e.g. `RHOAIENG-12345`) in the branch name.
3. **From conversation history**: Check if a Jira issue key was mentioned earlier in the conversation.
4. **Ask the user**: If none of the above yield a result, use `AskUserQuestion` to ask: "What Jira issue would you like to work on? (e.g. RHOAIENG-12345)"

### Phase 2: Identify the Working Repository

Determine the correct repository to work in:

1. **Check the current directory**: Run `git rev-parse --is-inside-work-tree 2>/dev/null` to see if we're in a git repo.
   - If yes, check if this looks like a project repo (has `package.json`, `go.mod`, `Makefile`, `pyproject.toml`, or `src/` directory). If so, use this directory.
   - If we're in a git repo but it looks like a config/skills/dotfiles repo (e.g. `claude-skills`, `.claude`), continue to step 2.
2. **Search for repo subdirectories**: If the current directory isn't a project repo, look for git repositories in subdirectories (one level deep). List any found and ask the user which one to work in using `AskUserQuestion`.
3. **Ask the user**: If no suitable repo is found, use `AskUserQuestion` to ask: "Which repository do you want to work in? Please provide the path."

### Phase 3: Validate Branch State

Ensure the working branch is clean and ready for development.

1. `cd` to the target repository (if not already there).
2. Run `git status --short` to check for uncommitted changes.
3. Run `git branch --show-current` to get the current branch name.
4. Check if the branch is up to date with the upstream main branch:
   - Run `git remote` to list remotes. If an `upstream` remote exists, use it; otherwise fall back to `origin`.
   - Run `git fetch <remote> main` using the chosen remote.
   - Run `git log HEAD..<remote>/main --oneline` to see if there are upstream commits not in the current branch.
5. **If there are uncommitted changes**, abort with a message:
   > "Your working tree has uncommitted changes. Please commit, stash, or discard them before starting work."
6. **If the branch is behind upstream main**, abort with a message:
   > "Your branch is behind upstream main. Please rebase or create a fresh branch from main before starting work."
7. **If the branch is `main` itself**, abort with a message:
   > "You're on the main branch. Please create a feature branch first (e.g. `git checkout -b RHOAIENG-12345`)."

### Phase 4: Gather Context

Read `~/.claude/skills/.context/jira-mcp.md` before making any Jira MCP calls.

#### Step 1: Fetch the Jira issue

Use `getJiraIssue` with the issue key and `responseContentFormat: "markdown"` to get the full issue details: summary, description, acceptance criteria, status, priority, issue type, and any linked issues.

#### Step 2: Check for linked PRs

Look at the Git Pull Request field for any existing PRs linked to this issue. If there are existing PRs, note them — they may provide context on prior work or related changes.

#### Step 3: Check for subtasks or parent issues

If the issue has a parent (epic or story), fetch the parent to understand the broader context. If the issue has subtasks, note them to understand the full scope.

#### Step 4: Read relevant comments

Use `getJiraIssue` or search for recent comments on the issue that might contain implementation notes, decisions, or context from teammates.

### Phase 5: Understand the Codebase Context

Based on the Jira issue details:

1. **Identify relevant areas of the codebase**: Search for files, components, or modules mentioned in the issue description or related to the feature area.
2. **Read key files**: Open and read the most relevant source files to understand the current state of the code.
3. **Check for related tests**: Find existing test files that cover the area being modified.

### Phase 6: Present Plan and Start Working

1. **Summarize the issue**: Present a concise summary of:
   - The Jira issue (key, title, type, priority)
   - What needs to be done (from the description and acceptance criteria)
   - The relevant code areas identified
   - Any linked PRs or related issues
2. **Propose an approach**: Outline the implementation plan — which files to modify, what changes to make, and in what order.
3. **Ask to proceed**: Use `AskUserQuestion` to confirm: "Ready to start implementing? Or would you like to adjust the plan?"
4. **Begin implementation**: Once confirmed, start making the changes.
