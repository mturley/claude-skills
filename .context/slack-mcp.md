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

### Scrum Channels (RHOAI Dashboard Team)

| Channel | ID | Focus Area |
|---------|----|-----------| 
| #wg-dashboard-green | `C07C0447EAV` | AI Hub (model registry/catalog) - Mike's scrum |
| #wg-dashboard-zaffre | `C069KSM8T9N` | Model Serving / Connections / Models-as-a-Service |
| #wg-dashboard-razzmatazz | `C069KSM8T9N` | Pipelines / Experimentation / Hardware Profiles |
| #wg-dashboard-monarch | `C07BFD5J4CB` | Dashboard Platform (modular architecture) |
| #wg-dashboard-crimson | `C099MEPGF43` | GenAI Studio (cross-functional with Llama Stack teams) |

See `people.md` for full scrum team rosters and member details.

### Team Channels

| Channel | ID | Purpose |
|---------|----|---------| 
| #team-openshift-ai-dashboard | `C05SMJ09DD2` | Main RHOAI Dashboard team channel (all scrums) |
| #forum-openshift-ai-dashboard | `C07CQ4R4HMY` | Discussion with people outside the dashboard team |
| #team-openshift-ai-dashboard-experiments | `C08N1JWJGPP` | Experimenting with AI tools |
| #team-ai-eng-all | `C07LJEHRV2R` | RHOAI-wide announcements (all backend teams, not just dashboard) |
| #openshift-ai-hub-devs | `C08G31WCV16` | AI Hub backend team collaboration |

### AI-Driven Development

| Channel | ID | Purpose |
|---------|----|---------| 
| #wg-ai-driven-development | `C0995TL0ZV3` | Tools for AI-driven development (Ambient Code Platform, etc.) |

### Build & Release Notifications

| Channel | ID | Purpose |
|---------|----|---------| 
| #odh-build-notifications | `C07ANR0T9KJ` | Automated ODH build notifications |
| #rhoai-build-notifications | `C07ANR2U56C` | Automated RHOAI build notifications |
| #wg-odh-nightly | `C077MU0JNN9` | ODH nightly build notifications and discussions |

### PatternFly (Design System)

| Channel | ID | Purpose |
|---------|----|---------| 
| #list-patternfly | `C04JMHKSD9C` | PatternFly support (large community channel) |
| #patternfly-release | `C04JTH3LQF6` | PatternFly release notifications and discussion |

### Office

| Channel | ID | Purpose |
|---------|----|---------| 
| #lowell-office | `C087YMZ0YJJ` | Lowell Red Hat office chat (Mike goes in once a week) |

## Usage Patterns

*TODO: Document how Mike uses Slack, notification preferences, etc.*

## Gotchas

- **Enterprise restriction (CRITICAL):** The Red Hat Slack workspace has `enterprise_is_restricted` security policy that blocks channel listing APIs when using browser session tokens. This means:
  - ❌ `list_joined_channels` returns empty (can't discover channels)
  - ❌ `get_channel_id_by_name` returns empty (can't look up by name)
  - ❌ `refresh_channel_cache` fails
  - ✅ `whoami` works (auth.test API not restricted)
  - ✅ `get_channel_history` works **if you already know the channel ID**
  - ✅ `get_thread`, `post_message`, etc. work **if you already know the channel ID**
  
  **Workaround:** Use channel IDs directly (see "Important Channels" above). Cannot discover channels via API - must know IDs in advance.

- **Session tokens:** Still uses browser session tokens (xoxc/xoxd) which previously caused auth lockout issues with community servers. Monitor for similar issues with the Red Hat internal server.
- **Token expiration:** Tokens expire when you log out of Slack in browser. Run refresh script if tools start failing with auth errors.
- **DM discovery:** Direct messages may not appear in channel listings without explicitly using `list_joined_channels` with `types="public_channel,private_channel,im,mpim"` (and even then, enterprise restriction applies).
