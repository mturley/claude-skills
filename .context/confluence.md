# Confluence Reference

Technical reference for working with Confluence on the RHOAI Dashboard team's spaces.

**Instance:** `redhat.atlassian.net`

## Access Methods

**Primary:** Use the Atlassian MCP server (`mcp__atlassian__*` tools). If the MCP server is disabled or unavailable, fall back to `curl`.

## Resolving User References (Legacy Data Center)

> **Note:** This section applied to Confluence Data Center (`spaces.redhat.com`). After the Cloud migration, user references may work differently. Verify and update as needed.

Confluence pages store user references as opaque user keys (e.g., `<ri:user ri:userkey="8a808dbe..." />`). On Data Center, these could be resolved via the REST API with a PAT. On Cloud, user resolution may be handled differently.

## Extracting Page IDs from URLs

Confluence page URLs contain the content ID. For example:
- URL: `https://spaces.redhat.com/spaces/RHODS/pages/479331996/Page+Title`
- Content ID: `479331996`

Use this ID to fetch the page content.
