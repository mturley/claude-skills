# Jira MCP Reference

Technical reference for using Jira MCP with the RHOAIENG project (RHOAI Dashboard team).

## Server Configuration

**Server:** Official Atlassian Cloud MCP (Streamable HTTP transport)
**Instance:** `redhat.atlassian.net`
**Cloud ID:** `2b9e35e3-6bd3-4cec-b838-f4249ee02432` (can also use `redhat.atlassian.net` as `cloudId` param)
**MCP server name:** `atlassian` (tools are `mcp__atlassian__*`)
**Auth:** OAuth via browser (no PAT needed)
**User identifiers:** Atlassian Cloud `accountId` (not DC usernames). Look up via `lookupJiraAccountId` with email. See `people.md` for team roster with accountIds.

> **Note:** SSE endpoint (`/v1/sse`) deprecated after June 30, 2026. We use Streamable HTTP (`/v1/mcp`) which is the recommended transport.

## Important Rules

- **Linking PRs to issues:** When asked to link/attach a PR to a Jira issue, ALWAYS use the Git Pull Request custom field (`customfield_10875`) via `editJiraIssue`. NEVER use `addCommentToJiraIssue` for this.
- **Custom fields not in getJiraIssue responses:** The official Atlassian Cloud MCP strips custom fields from issue responses. To read custom field values, use `searchJiraIssuesUsingJql` with explicit `fields` parameter, or use the REST API directly.

## Quick Reference

| Field | Custom Field ID | Format | Notes |
|-------|----------------|--------|-------|
| Team | `customfield_10001` | Object: `{"id": "..."}` | Atlassian Teams type, see IDs below |
| Priority | Built-in | Object: `{"id": "10003"}` | See Priority IDs below |
| Severity | `customfield_10840` | Object: `{"id": "19919"}` | Use option ID, see table below |
| Epic Link | `customfield_10014` | String: `"RHOAIENG-12345"` | Epic key |
| Parent Link | `customfield_10018` | String: `"RHOAIENG-12345"` | For hierarchy, NOT epics |
| Git Pull Request | `customfield_10875` | String: `"https://github.com/..."` | Manual only, doesn't auto-populate |
| Sprint | `customfield_10020` | Integer sprint ID | Extract from sprint search results |
| Story Points | `customfield_10028` | Integer or null | Story points estimate |
| Original Story Points | `customfield_10977` | Numeric or null | Original estimate before refinement |
| Blocked | `customfield_10517` | Object: `{"id": "10852"}` | True=10852, False=10853 |
| Blocked Reason | `customfield_10483` | String | "None" or actual reason text |
| Activity Type | `customfield_10464` | Object: `{"id": "12228"}` | See Activity Type IDs below |
| Flagged | `customfield_10021` | Array: `[{"id": "10019"}]` | Impediment |

---

## RHOAIENG Project Configuration

**Project Key:** `RHOAIENG`
**Project ID:** `10350`

**Creating issues (Cloud API):** Use `createJiraIssue` with:
- `projectKey`: `"RHOAIENG"`
- `issueTypeName`: `"Bug"`, `"Task"`, or `"Story"` (string names, not IDs)
- `assignee_account_id`: Cloud accountId from people.md
- `additional_fields`: object for custom fields (replaces DC's `customFields`)
- `contentFormat`: `"markdown"` (for markdown descriptions)

**Updating issues:** Use `editJiraIssue` with:
- `fields`: object containing field updates (replaces DC's `customFields`)
- `contentFormat`: `"markdown"`

**Issue Type IDs (for reference):**
- Bug: `10016`
- Task: `10014`
- Story: `10009`

### Dashboard Team Issues (default)

For issues owned by the RHOAI Dashboard team (UI/frontend work):

**Component:** AI Core Dashboard (ID `15570`)
**Team:** RHOAI Dashboard — `{"id": "ec74d716-af36-4b3c-950f-f79213d08f71-1809"}`
**Labels:**
- Model Registry only: `dashboard-area-model-registry`
- Model Catalog only: `dashboard-area-model-catalog`
- MCP (Catalog & Deployments): `dashboard-area-mcp`
- Multiple areas: Use multiple labels as needed

### AI Hub Team Issues

For issues owned by the RHOAI AI Hub team (operator, backend, infrastructure):

**Component:** AI Hub (ID `15556`)
**Team:** RHOAI AI Hub — `{"id": "ec74d716-af36-4b3c-950f-f79213d08f71-1712"}`
**Labels:** Typically none (no dashboard-area labels)

---

## Custom Fields Reference

### Team (customfield_10001)

**Type:** `atlassian-team` (Atlassian Teams integration)

**Format:** Object with `id` key
```json
{"id": "ec74d716-af36-4b3c-950f-f79213d08f71-1809"}
```

**Team IDs:**
| Team | ID |
|------|------|
| RHOAI Dashboard | `ec74d716-af36-4b3c-950f-f79213d08f71-1809` |
| RHOAI AI Hub | `ec74d716-af36-4b3c-950f-f79213d08f71-1712` |

---

### Priority

**Field:** Built-in priority field

**Format:** Object with id
```json
{"id": "10003"}
```

**Priority IDs:**
| Priority | ID |
|----------|------|
| Blocker | `10000` |
| Critical | `10001` |
| Major | `10002` |
| Normal | `10003` |
| Minor | `10004` |
| Undefined | `10005` |

---

### Severity (customfield_10840) - Bugs Only

**Format:** Object with `id` key (using the option ID number)
```json
// Correct
{"id": "19919"}
```

**Severity Values:**
| Value | ID |
|-------|------|
| Critical | `19917` |
| Important | `19918` |
| Moderate | `19919` |
| Low | `19920` |
| Informational | `19921` |

---

### Activity Type (customfield_10464)

**Format:** Object with `id` key (using the option ID number)
```json
{"id": "12228"}
```

**Activity Type Values:**
| Value | ID |
|-------|------|
| Tech Debt & Quality | `12228` |
| New Features | `12229` |
| Learning & Enablement | `12230` |

---

### Epic Link vs Parent Link

These are **completely different fields** - use the correct one:

| Field | ID | Purpose | Value Format |
|-------|--------|---------|--------------|
| **Epic Link** | `customfield_10014` | Link issue to an epic | String: `"RHOAIENG-27992"` |
| **Parent Link** | `customfield_10018` | Parent-child hierarchy | String: `"RHOAIENG-27992"` |

**Common Mistake:**
Using Parent Link when you meant Epic Link will NOT properly associate the issue with the epic. They serve different purposes in Jira's data model.

---

### Git Pull Request (customfield_10875)

**Value:** Full PR URL(s) as a string. Multiple PRs are comma-separated.

**When to use:** This field is for PRs that **fix** the issue. When the user asks to "link a PR to an issue", this is the field to update.

**When NOT to set:** Do not set this field when creating a new issue, even if a PR is mentioned in context. A PR that *caused* a bug is not the same as a PR that *fixes* it. Only populate this field when a fix PR exists or is being created for the issue.

**How to set:**
1. First, fetch the issue with `getJiraIssue` and check the current value of `customfield_10875`
2. If the field is empty/null, set it to the new PR URL
3. If the field already has a value, append the new URL as a comma-separated entry

```
// Single PR
"customfield_10875": "https://github.com/opendatahub-io/odh-dashboard/pull/6466"

// Multiple PRs (append to existing)
"customfield_10875": "https://github.com/opendatahub-io/odh-dashboard/pull/6466, https://github.com/kubeflow/model-registry/pull/2288"
```

Use `editJiraIssue` with the value in `fields`:
```
issueIdOrKey: "RHOAIENG-51543"
fields: {"customfield_10875": "<url or comma-separated urls>"}
```

**Important:** This field does NOT auto-populate from GitHub integrations. It must be set manually via the API.

---

### Sprint (customfield_10020)

**Value:** Integer sprint ID (e.g., `82844`)

**Important:** Sprint IDs must be extracted from search results. See "Finding Sprints" section below.

---

### Story Points (customfield_10028)

**Value:** Integer or null (e.g., `5`, `8`, `null`)

Standard story point estimate for the issue.

---

### Original Story Points (customfield_10977)

**Value:** Numeric or null

Represents the original estimate before sprint refinement. Useful for tracking estimation accuracy.

---

### Blocked (customfield_10517)

**Value:** Select field with object format
```json
{"id": "10852"}
```

| Value | ID |
|-------|------|
| True | `10852` |
| False | `10853` |

Used together with Blocked Reason.

---

### Blocked Reason (customfield_10483)

**Value:** String. `"None"` when not blocked, or actual reason text when blocked.

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

**For previous (most recently closed) sprint — two-step approach:**

Sprint names are inconsistent (e.g. `Dashboard - Green - 34` vs `Dashboard - Green-35`), so do NOT guess the exact sprint name. Instead:

1. Search for a recent issue from a closed Green sprint to discover the sprint name and ID:
```jql
project = RHOAIENG AND sprint in closedSprints() AND component = "AI Core Dashboard" AND labels = "dashboard-area-model-registry" ORDER BY updated DESC
```
2. Parse the `customfield_10020` sprint data from the first result to extract the sprint `id` and `name`.
3. Use the sprint ID (e.g. `sprint = 81753`) to query all issues from that sprint.

### Sprint Board URL

To link to a sprint's board view in Jira Cloud, use the board URL format:
```
https://redhat.atlassian.net/jira/software/c/projects/RHOAIENG/boards/{boardId}?sprint={sprintId}
```

**Parameters:**
- `boardId` — The board ID. For the AI Core Dashboard board: `1133`
- `sprint` — The sprint ID (integer, extracted from sprint field data)

---

### Parsing Sprint Data

On Cloud, the `customfield_10020` field returns sprint objects (not the DC string format):
```json
{"id": 17597, "name": "Dashboard - Green-35", "state": "active", "boardId": 1133}
```
Extract the `id` field to use when setting sprints on issues.

### Filtering for Team Sprints

Multiple scrum teams share the AI Core Dashboard board. Sprint naming patterns:
- **Green sprints:** `Dashboard - Green - N` or `Dashboard - Green-N` (Model Registry/Catalog team)
- **Razzmatazz sprints:** `Dashboard - Razzmatazz - N` (different team)
- **Monarch sprints:** `Dashboard - Monarch-N` (different team)

**Only use sprints matching your team's pattern.** For the Model Registry/Catalog team, filter for "Green" in the sprint name.

### Green Scrum Quick Filter

**Saved Filter ID:** TBD (DC filter `12439012` did not migrate — needs to be recreated or found on Cloud)

This saved filter contains the Green scrum's area labels. Use it in JQL queries instead of specifying individual `dashboard-area-*` labels:

```jql
filter = 12439012
```

**Example — Green scrum issues in current sprint:**
```jql
project = RHOAIENG AND sprint in openSprints() AND filter = 12439012 AND status = "Review" ORDER BY priority ASC
```

---

## Description Formatting

On Jira Cloud, use `contentFormat: "markdown"` to write descriptions in standard Markdown.

**File reference syntax (Markdown):**
- Basic file link: `[filename](https://github.com/OWNER/REPO/blob/main/path/to/file.ts)`
- Specific line: `[filename:L42](https://github.com/OWNER/REPO/blob/main/path/to/file.ts#L42)`
- Line range: `[filename:L42-L50](https://github.com/OWNER/REPO/blob/main/path/to/file.ts#L42-L50)`

---

## Write Operation Preview Requirement

**Before any Jira write operation** (`createJiraIssue`, `editJiraIssue`, `addCommentToJiraIssue`, `transitionJiraIssue`), always show the user a preview of what will be written. This includes:

- **Creating issues:** Show the full drafted title, description, and all fields (priority, severity, labels, sprint, assignee, etc.) before making the API call.
- **Updating issues:** Show a diff or summary of what fields/content will change.
- **Posting comments:** Show the full comment text.
- **Transitioning issues:** State the current status and the target status.

Wait for user approval before proceeding with the write operation.

---

## Troubleshooting

### `searchJiraIssuesUsingJql` maxResults Parameter
**Symptom:** `Input validation error: Expected number, received string` when passing `maxResults`

**Solution:** The `maxResults` parameter requires a strict number type. If validation fails, omit the parameter entirely (defaults to 10) rather than trying to cast or quote the value.

### Authentication Failures
**Symptom:** 401 Unauthorized or connection errors

**Solutions (Cloud):**
- Re-authenticate via browser when prompted by the OAuth flow
- Check `claude mcp list` to see if the server shows "Needs authentication"

---

## See Also

- **`/create-jira` skill:** [`~/git/claude-skills/create-jira/SKILL.md`](../create-jira/SKILL.md) - Skill that uses this reference to create RHOAI Dashboard issues
