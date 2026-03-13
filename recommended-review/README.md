# /recommended-review

Loads the [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app via Puppeteer and summarizes recommended actions for PR reviews and team work.

## Prerequisites

- The [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) app must be running locally at http://localhost:5173/ before invoking.
- Puppeteer MCP server configured and accessible.

## Usage

Run `/recommended-review` in any Claude Code session. No arguments needed.

The skill launches a headless browser, waits for the dashboard to finish loading all data (GitHub PRs, Jira sprint info, linked PRs), expands the recommended actions list, and presents a summary of what needs your attention. It then offers to help with the top-priority action.

## What it shows

- Recommended actions from the dashboard, summarized in a table
- Action type (Review PR, Re-review PR)
- PR details (number, title, repo, author)
- Jira priority and linked issue info (if available)
- An offer to help with the first recommended action
