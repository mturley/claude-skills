---
name: zaffreify
description: Use when setting up Jira issues for the Zaffre scrum team — sets component, team, labels, activity type, and optionally renames CLONE-prefixed issues across the issue and all its children/subtasks
---

# Zaffreify

Bulk-update a Jira issue and all its descendants to have the correct scrum team fields: component, team, labels, activity type, and naming convention.

Works on any issue type: epics (updates all tasks and subtasks underneath), stories/tasks/bugs (updates the issue and any subtasks).

**Technical Reference:** For field IDs, formats, and gotchas, see [`../.context/jira.md`](../.context/jira.md)

## Arguments

- `$ARGUMENTS` - Jira issue key (e.g. `RHOAIENG-76495`)

## Instructions

### 1. Validate input

If no issue key is provided, ask the user for the Jira issue key.

### 2. Fetch the issue

Fetch the issue details. Show the user the summary and issue type.

### 3. Collect all descendants

Depending on issue type:

**If Epic:** Find child issues via Epic Link, then find subtasks of those tasks if any:
```jql
"Epic Link" = <KEY> ORDER BY key ASC
```
Then for any issues found:
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

Query all collected issue keys with fields `summary`, `components`, `labels`, `customfield_10001` (Team), `customfield_10464` (Activity Type).

### 5. Ask which scrum team and area labels to apply

Run the label lookup script to fetch available labels dynamically from Jira:

```bash
~/git/claude-skills/zaffreify/jira-labels.sh scrum
~/git/claude-skills/zaffreify/jira-labels.sh area
```

If the script fails (missing `.env`, no API token, network error), fall back to these hardcoded lists:
- **Scrum:** `dashboard-zaffre-scrum`, `dashboard-crimson-scrum`, `dashboard-tangerine-scrum`, `dashboard-onyx-scrum`, `dashboard-razzmatazz-scrum`, `dashboard-green-scrum`, `dashboard-purple-scrum`, `dashboard-monarch-scrum`
- **Area:** `dashboard-area-model-serving`, `dashboard-area-model-registry`, `dashboard-area-pipelines`, `dashboard-area-workbenches`

**Scrum team** — present as a **single-select** AskUserQuestion using the scrum label list. Recommend `dashboard-zaffre-scrum`. The selected label determines both the label to apply and the team UUID (see Team Mapping table below).

**Area labels** — present as a **multi-select** AskUserQuestion using the area label list. Recommend `dashboard-area-model-serving`. Allow "Other" for custom labels.

### 5b. Ask about Activity Type

Ask the user (using AskUserQuestion) whether to set Activity Type to "New Features" on all issues. Default recommendation is yes.

- `Set Activity Type to "New Features"` (Recommended)
- `Leave Activity Type unchanged`

Note: The Activity Type field (`customfield_10464`) is not available on the Sub-task edit screen in Jira. If the user chooses to set it, only apply it to the epic and tasks — skip subtasks silently (they don't support this field).

### 6. Check for CLONE prefix and feature name placeholders

Scan all issue summaries for renaming needs. Two patterns to handle:

1. **`CLONE - ` prefix** — e.g. `CLONE - QE signoff`
2. **`[<Feature Name>]` placeholder** — e.g. `CLONE - [<Feature Name>]- Feature signoff - GA`

If either pattern is found in any summary:

- List the affected issues for the user
- Ask (using AskUserQuestion): "What is the feature name for these issues?" with a text input option
- The user's answer becomes the feature name (e.g. `Fast vLLM`)
- Apply renaming rules:
  - Replace `CLONE - [<Feature Name>]- ` with `<feature name> - ` (e.g. `Fast vLLM - Feature signoff - GA`)
  - Replace `CLONE - [<Feature Name>] - ` (with space before dash) the same way
  - Replace `CLONE - ` (without placeholder) with `<feature name> - ` (e.g. `Fast vLLM - QE signoff`)
  - Process the most specific pattern first (placeholder variants before bare CLONE prefix)

### 7. Preview changes

Show the user a table of all issues and what will change:

| Key | Summary | Component | Team | Labels to add | Activity Type |

For each issue, show:
- **Component:** current -> `AI Core Dashboard` (or "already set")
- **Team:** current -> selected team name (or "already set" / "inherited" for subtasks)
- **Labels:** which labels will be added (preserving any existing labels)
- **Summary:** old -> new (only if CLONE prefix is being replaced)
- **Activity Type:** current -> `New Features` (or "already set" / "n/a" for subtasks) — only if user opted in at step 5b

Wait for user approval before proceeding.

### 8. Apply changes

For each issue, build the update payload:

**Component:**
```json
{"components": [{"name": "AI Core Dashboard"}]}
```

**Team** (NOT subtasks — they inherit from parent). Use the UUID from the Team Mapping table below based on the scrum team selected in step 5:
```json
{"customfield_10001": "<TEAM_UUID>"}
```

**Labels** — merge with existing, never replace. Add the selected scrum team label plus the user-selected area labels to the existing labels array.

**Summary** — apply the renaming rules from step 6: replace `CLONE - [<Feature Name>]- ` or `CLONE - [<Feature Name>] - ` with `<feature name> - `, then replace any remaining `CLONE - ` with `<feature name> - `.

**Activity Type** (if user opted in at step 5b, NOT subtasks — the field is unavailable on their screen):
```json
{"customfield_10464": {"id": "12229"}}
```

Update each issue using the Jira API.

### 9. Report results

Show a summary of what was updated. If any subtask team updates fail with "inherits the team assignment from its parent", note it succeeded via inheritance.

## Field Reference

| Field | Value | Notes |
|-------|-------|-------|
| Component | `AI Core Dashboard` (ID `15570`) | Replaces any existing, including placeholder |
| Team | `customfield_10001` — plain UUID string | See Team Mapping below. Subtasks inherit. |
| Labels | selected scrum label + user-selected area labels | Added to existing, never replacing |
| Activity Type | `customfield_10464` with `{"id": "12229"}` (New Features) | Optional. Not available on Sub-task screen — skip subtasks. |

## Team Mapping

Maps the scrum team label (selected in step 5) to the Jira Team UUID for `customfield_10001`:

| Scrum Label | Jira Team Name | Team UUID |
|-------------|---------------|-----------|
| `dashboard-tangerine-scrum` | RHAI Tangerine | `9679da1b-1866-4348-b65c-5ba033e9b761` |
| `dashboard-crimson-scrum` | RHAI Crimson | `c6e27e7d-7675-4a9c-98cc-1625898636ba` |
| `dashboard-razzmatazz-scrum` | RHAI Razzmatazz | `a3b9f319-0849-47bb-a8ee-ac908b882105` |
| `dashboard-onyx-scrum` | RHAI Onyx | `2c35865b-83c2-4931-911f-041d57c82532` |
| `dashboard-zaffre-scrum` | RHAI Zaffre | `c1466179-4c13-43a4-895d-c632789ded28` |
| `dashboard-green-scrum` | RHAI Green | `cffa1fd0-e59a-4305-b39e-1d40ae31112e` |
| `dashboard-purple-scrum` | RHAI Purple | `2cddc7b3-7a62-4be8-942d-1e160767cef1` |
| `dashboard-monarch-scrum` | RHAI Monarch | `6cb9996b-0281-4bee-b062-611b1d2d1baa` |
| `dashboard-pewter-scrum` | *(unknown — look up UUID if needed)* | — |
| *(fallback)* | RHOAI Dashboard | `ec74d716-af36-4b3c-950f-f79213d08f71-1809` |

If a scrum label is selected that isn't in this table, warn the user that the Team UUID is unknown and ask them to provide it or skip setting the team field.

## Label Lookup Script

`jira-labels.sh` dynamically fetches label names from Jira using the autocomplete suggestions API (`GET /rest/api/2/jql/autocompletedata/suggestions?fieldName=labels&fieldValue=<prefix>`). It requires `~/git/claude-skills/.env` with `JIRA_EMAIL`, `JIRA_TOKEN`, and `JIRA_HOST`.

```bash
jira-labels.sh area   # lists all dashboard-area-* labels
jira-labels.sh scrum  # lists all dashboard-*-scrum labels
```
