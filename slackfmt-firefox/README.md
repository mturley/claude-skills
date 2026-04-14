# /slackfmt-firefox

Converts markdown to Slack's native rich text format using Firefox's Clipboard API. Use this when pasting into **Slack's web interface in Firefox**.

## Why This Skill Exists

The [slackfmt](https://github.com/cauethenorio/slackfmt) project provides excellent tools for converting markdown to Slack format:
- [CLI tool](https://www.npmjs.com/package/@slackfmt/cli): `npx @slackfmt/cli@latest`
- [Agent skill](https://skills.sh/cauethenorio/slackfmt/slackfmt): installable via `npx skills add`

However, these tools use **Chromium's clipboard format** (`org.chromium.web-custom-data`), which doesn't work when pasting into **Slack's web interface in Firefox** (which expects `org.mozilla.custom-clipdata`).

This skill is a **stopgap solution** that automates the [slackfmt web app](https://slackfmt.labs.caue.dev/) using Playwright Firefox. The web app's JavaScript Clipboard API automatically creates the correct format for whichever browser you're using.

## Installation

The skill is included in this repository. Since you have the entire repo symlinked to `~/.claude/skills`, no additional setup is needed.

### Prerequisites

1. **Playwright MCP server with Firefox** must be configured:
   ```bash
   claude mcp add -s user playwright-firefox -- /opt/homebrew/bin/playwright-mcp --browser firefox
   ```

2. **Install Firefox for Playwright**:
   ```bash
   npx @playwright/mcp install-browser firefox
   ```

## Usage

```bash
# From a file
/slackfmt-firefox path/to/notes.md

# From stdin
cat scrum-update.md | /slackfmt-firefox

# Inline markdown
/slackfmt-firefox "- **Bold**\n  - Nested item"
```

After running the skill, paste directly into Slack - you'll get native Slack bullets with proper nesting, clickable links, and code formatting.

## Supported Markdown

- **Lists**: `-` for bullets, with 2-space indentation for nesting
- **Links**: `[text](url)` → clickable Slack links
- **Code**: `` `inline code` `` → monospace text
- **Bold/Italic**: `**bold**` and `_italic_`
- **Code blocks**: ` ```language\ncode\n``` ` → formatted code blocks

## How It Works

1. Opens https://slackfmt.labs.caue.dev/ in a headless Firefox browser (via Playwright)
2. Fills the markdown textarea with your content
3. Clicks the "Copy" button
4. The web app's JavaScript puts the formatted content on your clipboard
5. You paste into Slack and get native formatting

## Future Plans

We explored building a direct CLI converter but ran into challenges with:
- Binary clipboard format differences between Chromium and Firefox
- Playwright's Clipboard API limitations in automation contexts
- Swift/Python clipboard format conversion complexity

For now, this automated web approach is reliable. In the future, we may revisit a native conversion tool.

## See Also

- **For Chrome/Slack desktop app**: Use the [slackfmt CLI](https://www.npmjs.com/package/@slackfmt/cli) or [agent skill](https://skills.sh/cauethenorio/slackfmt/slackfmt) instead
- [slackfmt GitHub repository](https://github.com/cauethenorio/slackfmt)
- [slackfmt web app](https://slackfmt.labs.caue.dev/)
