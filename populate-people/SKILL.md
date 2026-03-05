# Populate People

Generates or updates `.context/people.md` with RHOAI Dashboard team member information sourced from Confluence, Jira, and GitHub.

Technical Reference: Read `../.context/confluence-mcp.md` before using Confluence tools.

## Prerequisites

Before starting, verify you have access to:
1. **Confluence MCP** - `confluence_getContent` tool must be available
2. **Jira MCP** - `jira_searchIssues` tool must be available
3. **GitHub CLI** - `gh` command must work (run `gh auth status` to check)

If any prerequisite is missing, inform the user and stop.

## Overview

The team structure is defined on a Confluence page (content ID `479331996`). Team members are stored as opaque user key references that must be resolved to names, then cross-referenced against Jira (for emails and usernames) and GitHub (for GitHub usernames).

## Phase 1: Check for Existing File

1. Check if `.context/people.md` already exists.
2. If it exists, read and parse it:
   - Extract each person's scrum, Name, Role, Email, Jira, and GitHub values from the tables
   - Store this as the **existing roster** for comparison after fetching Confluence data
   - Tell the user you found an existing file and will check for changes
3. If it does not exist, tell the user you will generate it from scratch.

## Phase 2: Fetch Team Structure from Confluence

1. Use `confluence_getContent` to fetch content ID `479331996` with `expand=body.storage`.
2. The response contains an HTML table with rows for each scrum. Extract the following for each scrum:
   - **Scrum name** (Green, Razzmatazz, Zaffre, Monarch, Crimson, Teal, Indigo, Purple, Tangerine)
   - **Focus area** (from the "Team Links/Main area of focus" column)
   - **Developer user keys** from `<ri:user ri:userkey="..." />` tags in the Developers column
   - **Developer roles** noted in parentheses (lead, shared lead, scrum master, Staff Eng, QE, on loan, borrowed, etc.)
   - **QE user keys** from the Quality Engineers column
   - Some members are listed as plain text names without user keys (especially in Teal and Indigo)
3. Collect all unique user keys across all scrums.

## Phase 3: Resolve Confluence User Keys to Names

The Confluence MCP does not have a user lookup tool. Use the REST API directly.

1. Get the Confluence API token:
   ```bash
   TOKEN=$(python3 -c "import json; c=json.load(open('$HOME/.claude.json')); print(c['mcpServers']['confluence']['env']['CONFLUENCE_API_TOKEN'])")
   ```

2. Resolve user keys in batches to avoid rate limiting. For each user key:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" \
     "https://spaces.redhat.com/rest/api/user?key=<userkey>"
   ```
   Extract `displayName` and `username` from the JSON response.

3. **Rate limiting:** If you get HTTP 429, wait 5-10 seconds and retry. Process keys in batches of ~10 with a brief pause between batches.

4. Some user keys may return a response with empty `displayName` but still include the `username`. In that case, try the full JSON response — the name might be in a different structure. See the "Resolving User References" section in `../.context/confluence-mcp.md`.

## Phase 4: Compare and Determine Scope

1. If an existing roster was loaded in Phase 1, compare it against the Confluence data from Phases 2-3:
   - **New members:** People in Confluence not in the existing file — these need full Jira and GitHub lookups
   - **Removed members:** People in the existing file not in Confluence — these will be dropped
   - **Scrum changes:** People who moved between scrums — update their scrum placement, preserve their existing data
   - **Preserve existing data:** For members present in both, keep their Email, Jira, and GitHub values from the existing file
   - **Incomplete entries:** Existing members with blank Email or Jira cells need Jira lookups; existing members with blank GitHub cells need GitHub lookups
   - Report all changes to the user (new members, departures, scrum moves)

2. Build two lists:
   - **Need Jira lookup:** New members + existing members with blank Email or blank Jira
   - **Need GitHub lookup:** New members + existing members with blank GitHub

3. If no existing file was found, all members need both Jira and GitHub lookups.

## Phase 5: Look Up Jira Usernames and Emails

**Only perform lookups for people identified in Phase 4 as needing Jira data.** Skip anyone who already has both Email and Jira filled in from the existing file.

1. Search for issues in the current open sprints to discover assignee details:
   ```jql
   project = RHOAIENG AND sprint in openSprints() AND component = "AI Core Dashboard"
   ```
   Extract `assignee.name`, `assignee.displayName`, and `assignee.emailAddress` from each issue.

2. For any team members still not found as assignees, look them up directly via the Jira REST API:
   ```bash
   TOKEN_JIRA=$(python3 -c "import json; c=json.load(open('$HOME/.claude.json')); print(c['mcpServers']['jira']['env']['JIRA_API_TOKEN'])")
   curl -s -H "Authorization: Bearer $TOKEN_JIRA" \
     "https://issues.redhat.com/rest/api/2/user?username=<confluence_username>"
   ```
   The Confluence username and Jira username are usually the same.

3. Build a lookup table mapping each person to their email and Jira username.

## Phase 6: Find GitHub Usernames

**Only perform lookups for people identified in Phase 4 as needing GitHub data.** Skip anyone who already has a GitHub username from the existing file.

1. **Check contributor lists** for these repos using `gh api`:
   - `opendatahub-io/odh-dashboard` (primary — most team members contribute here)
   - `opendatahub-io/mod-arch-library` (Monarch/Indigo members)
   - `kubeflow/model-registry` (Green scrum members)

   ```bash
   gh api repos/opendatahub-io/odh-dashboard/contributors --paginate -q '.[].login'
   ```

2. **Verify matches** by checking GitHub user profiles:
   ```bash
   gh api "users/<login>" -q '"\(.login) | \(.name // "null") | \(.company // "null")"'
   ```
   Confirm the `name` matches the person's display name and `company` is "Red Hat" (or similar).

3. **Search by commit author name** for anyone not found in contributor lists:
   ```bash
   gh api "search/commits?q=author-name:<Name>+org:opendatahub-io&per_page=3" \
     -q '.items[] | "\(.author.login) | \(.commit.author.name) | \(.repository.name)"'
   ```

4. **Be mindful of GitHub API rate limits.** If you get rate-limited, wait 10 seconds before retrying. Do not make excessive parallel requests.

5. Leave the GitHub column blank for anyone you cannot confidently identify. Do not guess.

## Phase 7: Write the File

Write `.context/people.md` with the following structure:

```markdown
# RHOAI Dashboard Team

Last updated: YYYY-MM-DD

Run `/populate-people` to update this file.

## <Scrum Name> Scrum

Focus: <focus area>

| Name | Role | Email | Jira | GitHub |
|------|------|-------|------|--------|
| ... | ... | ... | ... | ... |
```

**Formatting rules:**
- Use today's date for "Last updated"
- One section per scrum with `## <Name> Scrum` heading
- Include a `Focus:` line under each heading (omit if unknown)
- Sort scrums in this order: Green, Razzmatazz, Zaffre, Monarch, Crimson, Teal, Indigo, Purple, Tangerine
- Within each table, list the lead/scrum master first, then devs, then QEs
- Note cross-scrum assignments in the Role column (e.g., "Staff Eng (also in Green)")
- Note temporary assignments (e.g., "borrowed from RHDH for 3.0-3.4")
- Leave cells blank (not "unknown" or "N/A") when data is unavailable

After writing the file, report a summary of the team roster to the user.
