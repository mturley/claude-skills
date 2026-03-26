# Obsolete Skills

These skills have been superseded by the [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app, which provides the same information in a persistent, auto-refreshing dashboard. The skills still work but will recommend using the dashboard instead when invoked.

## [/reviews-status](reviews-status/)

Shows the review status of open PRs across your work, your team's sprint, and your scrum members, cross-referenced with RHOAIENG Jira issues.

## [/sprint-status](sprint-status/)

Shows the current Green sprint status with all tickets grouped by workflow status, including Jira issue details and GitHub PR metadata.

## [/epic-status](epic-status/)

Shows all issues in a selected epic, discovered from the current Green sprint, with Jira details and GitHub PR metadata.

## [/activity](activity/)

Shows a combined chronological timeline of your Jira and GitHub activity, merged into a single day-grouped report.

## [/github-activity](github-activity/)

Shows a chronological timeline of your GitHub activity over a configurable time period.

## [/jira-activity](jira-activity/)

Shows a chronological timeline of your Jira activity (changelog actions and comments) over a configurable time period.

---

The following skills have been replaced by standalone CLI commands in [mturley/work-scripts](https://github.com/mturley/work-scripts):

## [/pr-worktree](pr-worktree/)

Creates an isolated git worktree for a pull request and opens it in a new editor window. Replaced by the `pr-worktree` CLI command.

## [/branch-worktree](branch-worktree/)

Creates an isolated git worktree for a new branch and opens it in a new editor window. Replaced by the `branch-worktree` CLI command.
