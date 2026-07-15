---
name: zaffreify
description: Use when setting up Jira issues for the Zaffre scrum team — sets component, team, labels, and optionally renames CLONE-prefixed issues across the issue and all its children/subtasks
---

# Zaffreify

Bulk-update a Jira issue and all its descendants to have the correct Zaffre scrum team fields: component, team, labels, and naming convention.

Works on any issue type: epics (updates all tasks and subtasks underneath), stories/tasks/bugs (updates the issue and any subtasks).

**Technical Reference:** For field IDs, formats, and gotchas, see [`../.context/jira-mcp.md`](../.context/jira-mcp.md)

## Arguments

- `$ARGUMENTS` - Jira issue key (e.g. `RHOAIENG-76495`)

## Instructions

### 1. Validate input

If no issue key is provided, ask the user for the Jira issue key.

### 2. Fetch the issue

Use `getJiraIssue` to fetch the issue. Show the user the summary and issue type.

### 3. Collect all descendants

Depending on issue type:

**If Epic:** Find tasks via Epic Link, then find subtasks of those tasks:
```jql
"Epic Link" = <KEY> ORDER BY key ASC
```
Then for any tasks found:
```jql
parent IN (<TASK_KEYS>) ORDER BY key ASC
```

**If Task/Story/Bug:** Find subtasks:
```jql
parent = <KEY> ORDER BY key ASC
```

**If Sub-task:** No descendants to find — just process the issue itself.

Collect the target issue plus all descendants into a single list.

### 4. Read current field values

Query all collected issue keys with fields `summary`, `components`, `labels`, `customfield_10001` (Team).

### 5. Ask which labels to apply

Always apply `dashboard-zaffre-scrum`. Then ask the user (using AskUserQuestion) which area label(s) to add. Offer common options:

- `dashboard-area-model-serving` (Recommended)
- `dashboard-area-model-registry`
- `dashboard-area-pipelines`
- `dashboard-area-workbenches`

Allow multiple selections and an "Other" option for custom labels.

### 6. Check for CLONE prefix

Scan all issue summaries for the prefix `CLONE - `. If any are found:

- List them for the user
- Ask (using AskUserQuestion): "What feature prefix should replace 'CLONE - '?" with a text input option
- The user's answer becomes the replacement prefix (e.g. `Fast vLLM`)
- Ensure the prefix ends with ` - ` when used in the summary (append if needed)

### 7. Preview changes

Show the user a table of all issues and what will change:

| Key | Summary | Component | Team | Labels to add |

For each issue, show:
- **Component:** current -> `AI Core Dashboard` (or "already set")
- **Team:** current -> `RHAI Zaffre` (or "already set" / "inherited" for subtasks)
- **Labels:** which labels will be added (preserving any existing labels)
- **Summary:** old -> new (only if CLONE prefix is being replaced)

Wait for user approval before proceeding.

### 8. Apply changes

For each issue, build the update payload:

**Component:**
```json
{"components": [{"name": "AI Core Dashboard"}]}
```

**Team** (NOT subtasks — they inherit from parent):
```json
{"customfield_10001": "c1466179-4c13-43a4-895d-c632789ded28"}
```

**Labels** — merge with existing, never replace. Add `dashboard-zaffre-scrum` plus the user-selected area labels to the existing labels array.

**Summary** — if the issue has `CLONE - ` prefix and the user provided a replacement, replace `CLONE - ` with the new prefix.

Use `editJiraIssue` for each issue.

### 9. Report results

Show a summary of what was updated. If any subtask team updates fail with "inherits the team assignment from its parent", note it succeeded via inheritance.

## Field Reference

| Field | Value | Notes |
|-------|-------|-------|
| Component | `AI Core Dashboard` (ID `15570`) | Replaces any existing, including placeholder |
| Team | `c1466179-4c13-43a4-895d-c632789ded28` | RHAI Zaffre. Plain string. Subtasks inherit. |
| Labels | `dashboard-zaffre-scrum` + user-selected area labels | Added to existing, never replacing |
