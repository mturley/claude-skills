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
- **No issue type prefix in titles:** Do NOT prefix issue summaries with `BUG:`, `TASK:`, or `STORY:`. The issue type is already captured by the `issueTypeName` field — repeating it in the title is redundant.

## Quick Reference

| Field | Custom Field ID | Format | Notes |
|-------|----------------|--------|-------|
| Team | `customfield_10001` | String: `"team-uuid"` | Plain string ID (NOT object), see IDs below |
| Priority | Built-in | Object: `{"id": "10003"}` | See Priority IDs below |
| Severity | `customfield_10840` | Object: `{"id": "19919"}` | Use option ID, see table below |
| Epic Link | `customfield_10014` | String: `"RHOAIENG-12345"` | Epic key |
| Parent Link | `customfield_10018` | String: `"RHOAIENG-12345"` | For hierarchy, NOT epics |
| Git Pull Request | `customfield_10875` | ADF document (read) / markdown string (write) | Manual only, see details below |
| Sprint | `customfield_10020` | Integer sprint ID | Extract from sprint search results |
| Story Points | `customfield_10028` | Integer or null | Story points estimate |
| Original Story Points | `customfield_10977` | Numeric or null | Original estimate before refinement |
| Blocked | `customfield_10517` | Object: `{"id": "10852"}` | True=10852, False=10853 |
| Blocked Reason | `customfield_10483` | ADF document (rich text) | Returns ADF on read; use `contentFormat: "markdown"` on write |
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

**Format:** Plain string (NOT an object — passing `{"id": "..."}` will fail with "Team id is not valid")
```json
"ec74d716-af36-4b3c-950f-f79213d08f71-1809"
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

**Type:** Rich text field (ADF on Jira Cloud)

**Reading:** On Cloud API v3, this field returns as an Atlassian Document Format (ADF) document, NOT a plain string. PR URLs appear in two different ADF node formats:

*Format 1 — text node with link mark* (set via API with raw ADF):
```json
{"type": "text", "text": "https://github.com/org/repo/pull/123",
 "marks": [{"type": "link", "attrs": {"href": "https://github.com/org/repo/pull/123"}}]}
```

*Format 2 — inlineCard / Smart Link* (set via Jira web UI):
```json
{"type": "inlineCard", "attrs": {"url": "https://github.com/org/repo/pull/123"}}
```

To extract URLs, check for both: `mark.attrs.href` on text nodes with link marks, and `node.attrs.url` on inlineCard nodes.

**When to use:** This field is for PRs that **fix** the issue. When the user asks to "link a PR to an issue", this is the field to update.

**When NOT to set:** Do not set this field when creating a new issue, even if a PR is mentioned in context. A PR that *caused* a bug is not the same as a PR that *fixes* it. Only populate this field when a fix PR exists or is being created for the issue.

**How to set:**

> **CRITICAL: This field is overwrite-only — always read before writing.** The API replaces the entire field value; it does not append. If you skip reading the current value, you will destroy existing PR links. Use `searchJiraIssuesUsingJql` with `fields: ["customfield_10875"]` and `responseContentFormat: "adf"` to read the current ADF content, then include all existing `inlineCard` nodes alongside the new one.

1. **Read the current value** using `searchJiraIssuesUsingJql` with `fields: ["customfield_10875"]` and `responseContentFormat: "adf"`. Extract any existing `inlineCard` URLs from the ADF content.
2. Use `editJiraIssue` with raw ADF (do NOT use `contentFormat: "markdown"` — it fails with "Operation value must be an Atlassian Document")
3. **Prefer `inlineCard` format** — this renders as a Smart Link in the Jira UI (showing PR title, status, etc.):

```json
fields: {
  "customfield_10875": {
    "version": 1,
    "type": "doc",
    "content": [{
      "type": "paragraph",
      "content": [
        {"type": "inlineCard", "attrs": {"url": "https://github.com/opendatahub-io/odh-dashboard/pull/6466"}},
        {"type": "hardBreak"},
        {"type": "inlineCard", "attrs": {"url": "https://github.com/kubeflow/model-registry/pull/2288"}}
      ]
    }]
  }
}
```

For a single PR URL, omit the `hardBreak` and second `inlineCard` node.

4. **Include ALL existing URLs plus the new one** in the value. Separate each with a `hardBreak` node.

**Important:** This field does NOT auto-populate from GitHub integrations. It must be set manually via the API.

**Searching by PR URL:** To find the Jira issue associated with a GitHub PR, search the Git Pull Request field using JQL text search (`~`). Use the repo path and PR number (not the full URL):
```jql
project = RHOAIENG AND "Git Pull Request" ~ "kubeflow/model-registry/pull/2302" ORDER BY updated DESC
```
This is more reliable than searching by title or description text, since the PR may not reference the Jira issue key (especially in upstream repos where Jira references are prohibited).

---

### Sprint (customfield_10020)

**Value:** Plain integer sprint ID (e.g., `82844`). Do NOT wrap in an object — passing `{"id": 17613}` will fail with "Number value expected as the Sprint id." Pass the integer directly: `17613`.

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

**Type:** Rich text field (ADF on Jira Cloud)

**Reading:** On Cloud API v3, this field returns as an ADF document (same format as description), not a plain string. Extract plain text by recursing through ADF nodes.

**Writing:** Use `contentFormat: "markdown"` with `editJiraIssue` and pass the reason as a markdown string.

---

## Finding Sprints

The Jira sprint field **does NOT support text search operators** like `~` or `*`. Queries like `sprint ~ "Green*"` will fail with:
```
The operator '~' is not supported by the 'sprint' field
```

### Workaround: Search for Issues in Sprints

Use `searchJiraIssuesUsingJql` (MCP) or `POST /rest/api/3/search/jql` (REST API) with the JQL queries below. Include `customfield_10020` in the fields list to get sprint data. See the REST API section for the correct POST syntax — the old `GET /rest/api/3/search` endpoint has been removed.

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

**Saved Filter ID:** `94935`

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

### `editJiraIssue` description must go inside `fields`
**Symptom:** `Input validation error: Required` for `fields`, or description silently ignored.

**Solution:** The `description` is NOT a top-level parameter on `editJiraIssue`. It must be passed inside the `fields` object:
```json
fields: {"description": "..."}
```
The `fields` parameter is required and must be an object (not a string). The `contentFormat` parameter IS top-level and controls how the description markdown is interpreted.

### Authentication Failures
**Symptom:** 401 Unauthorized or connection errors

**Solutions (Cloud):**
- Re-authenticate via browser when prompted by the OAuth flow
- Check `claude mcp list` to see if the server shows "Needs authentication"
- If MCP auth continues to fail, use the REST API fallback (see below)

---

## REST API Fallback

When the Atlassian MCP server's OAuth flow fails (e.g. "Access denied" errors, callback URL issues), fall back to direct REST API calls using `curl`.

### Setup

Credentials are stored in `~/git/claude-skills/.env` (gitignored). Source this file before making API calls:

```bash
source ~/git/claude-skills/.env
```

If the file is missing, ask the user to create it based on `~/git/claude-skills/.env.example`. The required variables are `JIRA_EMAIL`, `JIRA_TOKEN`, and `JIRA_HOST`.

### Authentication Header

All requests use Basic auth:
```bash
-H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)"
```

**IMPORTANT:** Always `source` the `.env` file in the same `bash` command as the `curl` call, so credentials are not echoed or stored in Claude's transcript. Combine them in a single Bash tool call.

### Common Operations

**Create an issue:**
```bash
source ~/git/claude-skills/.env && curl -s -X POST \
  "https://${JIRA_HOST}/rest/api/3/issue" \
  -H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)" \
  -H "Content-Type: application/json" \
  -d '{ "fields": { ... } }'
```
Use ADF format for the description (same as Jira Cloud v3 API). The response includes `key` (e.g. `RHOAIENG-12345`).

**Get an issue:**
```bash
source ~/git/claude-skills/.env && curl -s \
  "https://${JIRA_HOST}/rest/api/3/issue/RHOAIENG-12345" \
  -H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)"
```

**Edit an issue:**
```bash
source ~/git/claude-skills/.env && curl -s -X PUT \
  "https://${JIRA_HOST}/rest/api/3/issue/RHOAIENG-12345" \
  -H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)" \
  -H "Content-Type: application/json" \
  -d '{ "fields": { ... } }'
```

**Get transitions:**
```bash
source ~/git/claude-skills/.env && curl -s \
  "https://${JIRA_HOST}/rest/api/3/issue/RHOAIENG-12345/transitions" \
  -H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)"
```

**Transition an issue:**
```bash
source ~/git/claude-skills/.env && curl -s -X POST \
  "https://${JIRA_HOST}/rest/api/3/issue/RHOAIENG-12345/transitions" \
  -H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)" \
  -H "Content-Type: application/json" \
  -d '{"transition": {"id": "111"}}'
```

**Search with JQL:**

> **IMPORTANT:** The `GET /rest/api/3/search` endpoint has been removed. Use `POST /rest/api/3/search/jql` instead.

```bash
source ~/git/claude-skills/.env && curl -s -X POST \
  "https://${JIRA_HOST}/rest/api/3/search/jql" \
  -H "Authorization: Basic $(echo -n "${JIRA_EMAIL}:${JIRA_TOKEN}" | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = RHOAIENG AND key = RHOAIENG-12345",
    "fields": ["summary", "status", "customfield_10020"],
    "maxResults": 1
  }'
```

### Notes

- The REST API uses the same field IDs, formats, and values documented above for the MCP tools
- Descriptions must be in ADF (Atlassian Document Format) JSON — the REST API v3 does not accept markdown directly
- HTTP 204 on transitions means success (no response body)
- HTTP 201 on issue creation means success (response includes `id`, `key`, `self`)
- Always prefer MCP tools when they're working — only fall back to REST when MCP auth fails

---

## See Also

- **`/create-jira` skill:** [`~/git/claude-skills/create-jira/SKILL.md`](../create-jira/SKILL.md) - Skill that uses this reference to create RHOAI Dashboard issues
