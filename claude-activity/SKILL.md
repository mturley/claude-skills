# Claude Activity

Summarize what was accomplished across all Claude Code sessions for a given day.

## Arguments

- An optional date in YYYY-MM-DD format (defaults to today)

## Instructions

1. **Run the extraction script**

   The script scans all `~/.claude/projects/` session files, extracts user messages,
   and outputs a structured summary grouped by project:

   ```bash
   python3 ~/.claude/skills/claude-activity/extract-sessions.py [YYYY-MM-DD]
   ```

   If no date argument was provided by the user, omit it (defaults to today).

2. **Analyze the output and summarize**

   The script output shows every user message from every session, grouped by project.
   Use this raw data to write a concise summary of accomplishments organized by project/theme.

   For each project, describe:
   - What was worked on (PRs reviewed, issues created, features built, bugs fixed, etc.)
   - Key outcomes (PR URLs, Jira issue keys, repos created, etc.)
   - Notable decisions made

   Keep it concise -- focus on outcomes, not the back-and-forth of the conversation.
   Combine related sessions (e.g. multiple sessions in the same project working on the same thing).

3. **Report the summary to the user**

   Present the summary as a readable report. Include:
   - A header with the date and total session/project counts
   - Sections grouped by project or theme
   - Bullet points for specific accomplishments
   - Links to PRs, issues, or repos when visible in the session data
