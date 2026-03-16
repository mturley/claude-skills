# Confluence MCP Reference

Technical reference for using Confluence MCP with the RHOAI Dashboard team's Confluence spaces.

## Server Configuration

**Server:** Official Atlassian Cloud MCP (Streamable HTTP transport) — same server as Jira
**Instance:** `redhat.atlassian.net`
**MCP server name:** `atlassian` (shared with Jira, tools are `mcp__atlassian__*`)
**Auth:** OAuth via browser (no PAT needed)

## Resolving User References (Legacy Data Center)

> **Note:** This section applied to Confluence Data Center (`spaces.redhat.com`). After the Cloud migration, user references may work differently. Verify and update as needed.

Confluence pages store user references as opaque user keys (e.g., `<ri:user ri:userkey="8a808dbe..." />`). On Data Center, these could be resolved via the REST API with a PAT. On Cloud, user resolution may be handled differently by the official Atlassian MCP.

## Extracting Page IDs from URLs

Confluence page URLs contain the content ID. For example:
- URL: `https://spaces.redhat.com/spaces/RHODS/pages/479331996/Page+Title`
- Content ID: `479331996`

Use this ID with `confluence_getContent` to fetch the page.
