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

### Closing the browser when done

When the browser testing goal appears to be accomplished (e.g., a visual verification is complete, a feature has been confirmed working, or the user says they're done with browser testing), **always offer to close the Playwright session** before finishing:

> "The browser testing looks complete. Would you like me to close the browser session?"

If the user agrees, close the browser with `browser_close`. If they decline, leave it open.
