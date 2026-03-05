# Confluence MCP Reference

Technical reference for using the Confluence Data Center MCP (`@atlassian-dc-mcp/confluence`) with spaces.redhat.com.

## Resolving User References

Confluence pages store user references as opaque user keys (e.g., `<ri:user ri:userkey="8a808dbe..." />`). The MCP server does NOT provide a user lookup tool, but the Confluence REST API supports it directly.

To resolve a user key to a display name, use curl with the PAT from the MCP config:

```bash
curl -s -H "Authorization: Bearer $CONFLUENCE_API_TOKEN" \
  "https://spaces.redhat.com/rest/api/user?key=<userkey>" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('displayName','UNKNOWN'))"
```

To resolve multiple user keys at once:

```bash
TOKEN="$CONFLUENCE_API_TOKEN"
for key in <key1> <key2> <key3>; do
  name=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "https://spaces.redhat.com/rest/api/user?key=$key" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('displayName','UNKNOWN'))" 2>/dev/null)
  echo "$key -> $name"
done
```

The token value can be found in `~/.claude.json` under `mcpServers.confluence.env.CONFLUENCE_API_TOKEN`.

## Extracting Page IDs from URLs

Confluence page URLs contain the content ID. For example:
- URL: `https://spaces.redhat.com/spaces/RHODS/pages/479331996/Page+Title`
- Content ID: `479331996`

Use this ID with `confluence_getContent` to fetch the page.
