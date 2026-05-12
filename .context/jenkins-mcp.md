# Jenkins MCP Reference

Technical reference for using Jenkins MCP with the RHOAI Dashboard team's CI.

## Server Configuration

**Instance:** `jenkins-csb-rhods-opendatascience` at `https://jenkins-csb-rhods-opendatascience.dno.corp.redhat.com`
**MCP server name:** `jenkins` (tools are `mcp__jenkins__*`)

## Key Jobs

| Job path | Use when |
|----------|----------|
| `components/dashboard/dashboard-e2e-tests` | User asks about E2E tests, test results, test failures, or CI status for the dashboard |

## Gotchas

- **Job search is shallow:** `jenkins_search_jobs` only matches top-level job names. For nested jobs (like `components/dashboard/dashboard-e2e-tests`), use the full folder path directly with tools like `jenkins_get_recent_builds` — don't rely on search to find them.
