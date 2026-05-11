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

## Gotchas

(To be filled in as issues are discovered)
