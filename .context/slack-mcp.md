# Slack MCP Reference

Technical reference for using Slack MCP with the Red Hat Slack workspace.

## Server Configuration

**Server:** Red Hat internal Slack MCP (`redhat-community-ai-tools/slack-mcp`)
**Instance:** Red Hat Slack workspace
**MCP server name:** `slack` (tools are `mcp__slack__*`)
**Auth:** Browser session tokens (xoxc/xoxd), auto-extracted via Playwright
**Deployment:** Podman container at `quay.io/redhat-ai-tools/slack-mcp`
**Username:** `mturley`

## Token Management

Tokens are browser session-based and expire periodically. To refresh:

```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/redhat-community-ai-tools/slack-mcp/main/scripts/setup-slack-mcp.py) --refresh-tokens
```

## Important Channels

*TODO: Document important channels, team communication patterns, and usage conventions.*

## Usage Patterns

*TODO: Document how Mike uses Slack, which channels to monitor, notification preferences, etc.*

## Gotchas

- **Session tokens:** Still uses browser session tokens (xoxc/xoxd) which previously caused auth lockout issues with community servers. Monitor for similar issues with the Red Hat internal server.
- **Token expiration:** Tokens expire when you log out of Slack in browser. Run refresh script if tools start failing with auth errors.
- **DM discovery:** Direct messages may not appear in channel listings without explicitly using `list_joined_channels` with `types="public_channel,private_channel,im,mpim"`.
