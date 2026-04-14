---
name: slackfmt-firefox
description: Format Markdown for Slack (Firefox) - Convert markdown to Slack's native rich text format using Firefox's Clipboard API
---

# Format Markdown for Slack (Firefox)

Convert markdown to Slack's native rich text format and copy to clipboard using Firefox's Clipboard API. Works with Slack's web interface in Firefox.

## Arguments

- `$ARGUMENTS` - Path to a markdown file, or markdown content from stdin. If no arguments, reads from stdin.

## Prerequisites

- Playwright MCP server configured with Firefox: `claude mcp list` should show `playwright-firefox`
- Firefox browser installed for Playwright: `npx @playwright/mcp install-browser firefox`

## Background

This skill uses the [slackfmt](https://github.com/cauethenorio/slackfmt) web application to convert markdown to Slack's clipboard format. The [slackfmt CLI](https://www.npmjs.com/package/@slackfmt/cli) and [agent skill](https://skills.sh/cauethenorio/slackfmt/slackfmt) work well for Chrome/Chromium-based browsers and the Slack desktop app, but **do not work with Slack's web interface in Firefox** because they use different clipboard formats:

- **Chromium/Chrome**: Uses `org.chromium.web-custom-data` clipboard type
- **Firefox**: Uses `org.mozilla.custom-clipdata` clipboard type

We explored various approaches to convert the slackfmt CLI's output to Firefox's format:
- ✗ Direct clipboard format conversion (Swift/Python) - binary format proved difficult
- ✗ Playwright's Clipboard API - `ClipboardItem` not available in automation context
- ✓ **slackfmt web app** - Uses JavaScript's Clipboard API which automatically creates the correct format for the browser

This skill is a **stopgap solution** until we can implement a proper command-line conversion tool. For now, it automates the slackfmt web workflow using Playwright Firefox.

## Instructions

### Phase 1: Get Markdown Content

1. If `$ARGUMENTS` is provided and is a file path, read the file
2. If `$ARGUMENTS` is provided but is not a file path, treat it as markdown content directly
3. If no `$ARGUMENTS`, read from stdin (check if stdin is available)
4. Store the markdown content for use in Phase 2

### Phase 2: Navigate to slackfmt Web App

Using the Playwright Firefox MCP tools:

1. Navigate to https://slackfmt.labs.caue.dev/
   ```
   mcp__playwright-firefox__browser_navigate(url: "https://slackfmt.labs.caue.dev/")
   ```

2. Wait for the page to load and take a snapshot to get element references
   ```
   mcp__playwright-firefox__browser_snapshot()
   ```

3. Locate the markdown input textarea (look for `textbox "Markdown input"` in the snapshot)

### Phase 3: Fill Markdown and Copy

1. Type the markdown content into the textarea using the ref from the snapshot:
   ```
   mcp__playwright-firefox__browser_type(
     ref: "<textarea-ref>",
     element: "Markdown input textbox",
     text: "<markdown-content>"
   )
   ```

2. Take another snapshot to locate the "Copy" button

3. Click the "Copy" button using its ref:
   ```
   mcp__playwright-firefox__browser_click(
     ref: "<copy-button-ref>",
     element: "Copy button"
   )
   ```

### Phase 4: Confirm Success

Tell the user:

```
✓ Copied to clipboard! The markdown has been converted to Slack's format and is ready to paste.

Paste into Slack now - you should see native Slack bullets with proper nesting and formatting.
```

### Phase 5: Clean Up

Close the browser:
```
mcp__playwright-firefox__browser_close()
```

## Example

```bash
# From a file
/slackfmt-firefox /tmp/scrum-update.md

# From stdin
cat notes.md | /slackfmt-firefox

# Inline markdown
/slackfmt-firefox "- **Bold item**\n  - Nested item with [link](https://example.com)"
```

## Notes

- The slackfmt web app processes everything client-side - your content never leaves the browser
- The app automatically converts markdown links `[text](url)` to clickable Slack links
- Inline code `` `code` `` becomes monospace formatted text
- Nested lists use 2-space indentation
- The preview pane shows how it will look in Slack before copying

## See Also

- [slackfmt GitHub repository](https://github.com/cauethenorio/slackfmt)
- [slackfmt web app](https://slackfmt.labs.caue.dev/)
- [slackfmt CLI (for Chrome/desktop)](https://www.npmjs.com/package/@slackfmt/cli)
- [slackfmt agent skill (for Chrome/desktop)](https://skills.sh/cauethenorio/slackfmt/slackfmt)
