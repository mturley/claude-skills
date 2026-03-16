# /email-triage

Scans your unread Gmail for important emails that need attention, filtering out noise from mailing lists, bots, calendar invitations, and expired reminders.

## What it does

1. Searches unread email using multiple strategies (direct messages, action-required keywords, Gmail importance signals, @-mentions)
2. Deduplicates and filters out noise (calendar invites, bot notifications, marketing, old mailing list threads)
3. Categorizes remaining emails by urgency: **Needs Action NOW**, **Should Respond Soon**, **Overdue / Check Status**, and **FYI / Can Safely Archive**
4. Presents a scannable report with one-line summaries and deadlines

## Requirements

- **Google Workspace MCP server** must be configured and authenticated (e.g., `@dguido/google-workspace-mcp`)

## Installation

```bash
ln -s ~/git/claude-skills/email-triage ~/.claude/skills/email-triage
```

## Usage

```
/email-triage
```

No arguments needed. The skill searches the last 30-90 days of unread email depending on the query type.
