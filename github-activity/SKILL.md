# GitHub Activity

**This skill is obsolete.** The [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) web app now provides the same information in a persistent, auto-refreshing dashboard. Before proceeding, tell the user about pr-reviews-dashboard and recommend using it instead. Then use AskUserQuestion to ask if they want to proceed with this skill anyway.

---

Show a chronological timeline of your GitHub activity over a configurable time period, formatted as day-grouped tables with PR titles, commit messages, and links.

**Optional argument:** Number of days (default: 7). Example: `/github-activity 14`

## Instructions

### Phase 1: Fetch, Enrich, and Render

Detect the GitHub username and run the pipeline in a single Bash call:

```bash
GHUSER=$(gh api user --jq '.login') && echo "{\"username\": \"$GHUSER\", \"days\": <N>}" | python3 ~/.claude/skills/github-activity/fetch-github-activity.py | python3 ~/.claude/skills/github-activity/render-github-activity.py
```

Replace `<N>` with the number of days from the argument (default: 7).

If the output is too large for the tool result, it will be persisted to a file. Read the file and output its contents.

**IMPORTANT:** Output the rendered report directly as text in the chat so the user can read it. Do NOT just leave the output in the tool result — the user cannot see tool results.

## Output Format

The report contains:
- **Day-grouped tables** with columns: Time (12-hour ET) | Author | PR / Branch | Action
- **Push events** show the commit SHA link and first line of the commit message
- **Non-main branch pushes** link to their associated PR (with title) when one exists
- **Review events** are consolidated — individual review comments are rolled up into their parent review submission (e.g. "Requested changes (12 comments)")
- **Summary section** at the end with PR counts, approvals, change requests, and commits per repo

## Important Notes

- The fetch script handles all GitHub API enrichment (PR titles, commit messages, branch-to-PR lookups) in parallel — no additional API calls are needed.
- Never use inline Python. All Bash commands must pipe to the skill helper scripts so they match the auto-approved permission patterns `echo *| python3 *github-activity/*` and `cat *| python3 *github-activity/*`.
- The report is read-only — do not modify any PRs or issues.
