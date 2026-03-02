# Jira MCP Reference

Technical reference for using Jira MCP with the RHOAIENG project (RHOAI Dashboard team).

## Quick Reference

| Field | Custom Field ID | Format | Notes |
|-------|----------------|--------|-------|
| Team | `customfield_12313240` | String: `"4158"` | NOT an object |
| Priority | Built-in | Object: `{"id": "1"}` | See Priority IDs below |
| Severity | `customfield_12316142` | Object: `{"id": "26752"}` | Use option ID, see table below |
| Epic Link | `customfield_12311140` | String: `"RHOAIENG-12345"` | Epic key |
| Parent Link | `customfield_12313140` | String: `"RHOAIENG-12345"` | For hierarchy, NOT epics |
| Git Pull Request | `customfield_12310220` | String: `"https://github.com/..."` | Manual only, doesn't auto-populate |
| Sprint | `customfield_12310940` | Integer: `82844` | Extract from sprint search results |

---

## RHOAIENG Project Configuration

**Project ID:** `12340620`

**IMPORTANT:** The project ID must ALSO be included in customFields as `"project": {"id": "12340620"}` when creating issues. The `projectId` parameter alone is not sufficient.

**Component:** AI Core Dashboard (include via `customFields`)

**Issue Type IDs:**
- Bug: `1`
- Task: `3`
- Story: `17`

**Labels:**
- Model Registry only: `dashboard-area-model-registry`
- Model Catalog only: `dashboard-area-model-catalog`
- Both: Use both labels

---

## Custom Fields Reference

### Team (customfield_12313240)

**Value:** `"4158"` (RHOAI Dashboard)

**Format:** String, NOT an object
```json
// ✅ Correct
"customfield_12313240": "4158"

// ❌ Wrong - will fail
"customfield_12313240": {"id": "4158"}
```

---

### Priority

**Field:** Built-in priority field

**Format:** Object with id
```json
{"id": "1"}
```

**Priority IDs:**
| Priority | ID |
|----------|------|
| Blocker | `1` |
| Critical | `2` |
| Major | `3` |
| Minor | `4` |
| Normal | `10200` |
| Undefined | `10300` |

---

### Severity (customfield_12316142) - Bugs Only

**Format:** Object with `id` key (using the option ID number)
```json
// ✅ Correct
{"id": "26752"}

// ❌ Wrong - will fail with "Option id 'null' is not valid"
{"value": "Moderate"}
{"name": "Moderate"}
```

**Severity Values:**
| Value | ID |
|-------|------|
| Urgent | `26749` (unverified) |
| Critical | `26750` |
| Moderate | `26752` |
| Low | `26753` |

---

### Epic Link vs Parent Link

These are **completely different fields** - use the correct one:

| Field | ID | Purpose | Value Format |
|-------|--------|---------|--------------|
| **Epic Link** | `customfield_12311140` | Link issue to an epic | String: `"RHOAIENG-27992"` |
| **Parent Link** | `customfield_12313140` | Parent-child hierarchy | String: `"RHOAIENG-27992"` |

**Common Mistake:**
Using Parent Link when you meant Epic Link will NOT properly associate the issue with the epic. They serve different purposes in Jira's data model.

---

### Git Pull Request (customfield_12310220)

**Value:** Full PR URL as string
```json
"https://github.com/kubeflow/model-registry/pull/2288"
```

**Important:** This field does NOT auto-populate from GitHub integrations. It must be set manually using `jira_updateIssue` when a PR exists.

---

### Sprint (customfield_12310940)

**Value:** Integer sprint ID (e.g., `82844`)

**Important:** Sprint IDs must be extracted from search results. See "Finding Sprints" section below.

---

## Finding Sprints

The Jira sprint field **does NOT support text search operators** like `~` or `*`. Queries like `sprint ~ "Green*"` will fail with:
```
The operator '~' is not supported by the 'sprint' field
```

### Workaround: Search for Issues in Sprints

**For current sprint** (search for issues in open sprints):
```jql
project = RHOAIENG AND sprint in openSprints() AND labels = "dashboard-area-model-registry" ORDER BY created DESC
```

**For next sprint** (search for issues in future sprints):
```jql
project = RHOAIENG AND component = "AI Core Dashboard" AND sprint in futureSprints() ORDER BY created DESC
```

### Parsing Sprint Data

The `customfield_12310940` field contains sprint data as strings like:
```
com.atlassian.greenhopper.service.sprint.Sprint@...[id=82844,rapidViewId=18687,state=FUTURE,name=Dashboard - Green-35,...]
```

**To extract sprint ID:**
1. Parse the sprint string from search results
2. Extract the `id=XXXXX` value
3. Use the integer ID when updating issues

### Filtering for Team Sprints

Multiple scrum teams share the AI Core Dashboard board. Sprint naming patterns:
- **Green sprints:** `Dashboard - Green - N` or `Dashboard - Green-N` (Model Registry/Catalog team)
- **Razzmatazz sprints:** `Dashboard - Razzmatazz - N` (different team)
- **Monarch sprints:** `Dashboard - Monarch-N` (different team)

**Only use sprints matching your team's pattern.** For the Model Registry/Catalog team, filter for "Green" in the sprint name.

---

## Jira Wiki Markup

When creating issue descriptions with file references, use Jira Wiki Markup syntax:

**File reference syntax:**
- Basic file link: `[filename|https://github.com/OWNER/REPO/blob/main/path/to/file.ts]`
- Specific line: `[filename:L42|https://github.com/OWNER/REPO/blob/main/path/to/file.ts#L42]`
- Line range: `[filename:L42-L50|https://github.com/OWNER/REPO/blob/main/path/to/file.ts#L42-L50]`

**Note:** Use Jira Wiki Markup link syntax `[text|url]`, NOT Markdown syntax `[text](url)`.

---

## Troubleshooting

### Authentication Failures
**Symptom:** 401 Unauthorized or connection errors

**Solutions:**
- Verify API token is valid and not expired
- Check JIRA_HOST environment variable is domain only (e.g., `issues.redhat.com` not `https://issues.redhat.com`)

---

## See Also

- **`/create-jira` skill:** [`~/git/claude-skills/create-jira/SKILL.md`](../create-jira/SKILL.md) - Skill that uses this reference to create RHOAI Dashboard issues