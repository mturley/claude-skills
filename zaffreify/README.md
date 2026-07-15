# zaffreify

Bulk-update a Jira issue and all its descendants to have the correct Zaffre scrum team fields.

## Usage

```
/zaffreify RHOAIENG-76495
```

## What it does

1. Fetches the given issue and walks all children (tasks under epics, subtasks under tasks)
2. Asks which area labels to apply (e.g. `dashboard-area-model-serving`)
3. If any issues have `CLONE - ` in the summary, asks for a feature prefix to replace it
4. Previews all changes and waits for approval
5. Sets on every issue: component (`AI Core Dashboard`), team (`RHAI Zaffre`), and the selected labels — merged with any existing labels
6. Subtasks inherit team from their parent automatically

## Requirements

- Atlassian MCP server must be enabled and authenticated
- Issue must be in the RHOAIENG project
