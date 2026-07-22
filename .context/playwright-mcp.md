# Playwright MCP Server

## Overview

The Playwright MCP server provides browser automation capabilities through both Chrome and Firefox instances. Each browser type has its own set of tools prefixed with `mcp__playwright-chrome__` or `mcp__playwright-firefox__`.

## Usage Patterns

### ODH Dashboard Impersonation

When using Playwright with odh-dashboard, if instructed to "use impersonation" or "impersonate":

1. After opening the odh-dashboard UI, locate the `#user-menu-toggle` menu in the top-right
2. Click "Start impersonate" from the menu
3. Wait until the "Stop impersonate" button becomes visible before proceeding

### ODH Dashboard Feature Flags

When using Playwright with odh-dashboard, if instructed to enable a feature flag or if testing requires a feature flag:

- Use the `devFeatureFlags` URL parameter when first navigating to the UI
- Format: `?devFeatureFlags=flagName=true`
- Multiple flags can be comma-separated: `?devFeatureFlags=flag1=true,flag2=true`
- Examples:
  - Single flag: `?devFeatureFlags=nimWizard=true`
  - Multiple flags: `?devFeatureFlags=deploymentWizardYAMLViewer=true,vLLMDeploymentOnMaaS=true`
- Only include these in the first navigation per session - the UI retains flags across page navigation

## Destructive Actions

Before clicking any element that could modify or destroy data — delete buttons, confirm dialogs for destructive operations, form submissions that create/update/delete resources, or any action that cannot be easily undone — **stop and ask the user for confirmation**. This applies even when the user has asked you to test a flow end-to-end. Navigation, opening modals, filling fields, toggling switches, and dismissing dialogs (cancel/close) are fine without asking.

The user can grant blanket approval for destructive actions during a single round of testing (e.g. "go ahead and click through everything without asking"). This approval expires when that testing round is complete — do not carry it forward to later testing.

## Screenshots

**MANDATORY: Always take screenshots in a subagent.** Screenshot data is large and pollutes the main conversation context. When you need to take a screenshot:

1. Spawn a subagent (using the `Agent` tool with `model: "sonnet"`) that takes the screenshot via `mcp__playwright-chrome__browser_take_screenshot` or `mcp__playwright-firefox__browser_take_screenshot`
2. In the subagent prompt, describe what you are looking for or trying to verify (if anything) so the subagent can inspect the screenshot and report back
3. The subagent should return: the file path of the saved screenshot, a short summary of what is visible, and the results of any specific inspection requested
4. Never call `browser_take_screenshot` directly from the main conversation — always delegate to a subagent

Example subagent prompt:
> "Take a screenshot of the current Playwright Chrome page. Describe what you see on the page. Specifically, check whether the model serving form has a 'Deploy' button visible and whether there are any error messages shown."

This keeps screenshot image data confined to the subagent's context and out of the main conversation.

## Session Lifecycle

### Recovering from a closed browser context

If the browser was closed unexpectedly (machine went to sleep, user quit the browser, etc.), subsequent tool calls will fail with errors like:

- `Target page, context or browser has been closed`
- `No open pages available`

When this happens:

1. Call `browser_close` on the affected MCP server (e.g. `mcp__playwright-chrome__browser_close`) — this resets the server's internal state even though the browser is already gone.
2. Then call `browser_navigate` on the same server to start a fresh session.

Do NOT keep retrying `browser_navigate` without closing first — the MCP server still holds a reference to the dead context and will keep erroring until you close it.

### Closing the browser when done

When the browser testing goal appears to be accomplished (e.g., a visual verification is complete, a feature has been confirmed working, or the user says they're done with browser testing), **always offer to close the Playwright session** before finishing:

> "The browser testing looks complete. Would you like me to close the browser session?"

If the user agrees, close the browser with `browser_close`. If they decline, leave it open.
