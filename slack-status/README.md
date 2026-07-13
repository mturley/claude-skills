# slack-status

Fetches and summarizes the two most recent Zaffre scrum status sync threads from `#wg-dashboard-zaffre`, and optionally watches the latest thread for new replies.

## Usage

```
/slack-status
```

## What it does

1. Searches `#wg-dashboard-zaffre` for the two most recent Slackbot status reminders ("Slack scrum sync!")
2. Fetches all replies to both threads
3. Summarizes each thread: participants, what each person was working on, blockers, key PRs/Jira links
4. Offers to watch the latest thread — if accepted, sets a 20-minute cron to check for new replies
5. While watching: summarizes new replies whenever the user sends a prompt

## Requirements

- Slack MCP server must be enabled and authenticated
- Channel ID `C069KSM8T9N` must be accessible (it's hardcoded to avoid the Red Hat enterprise channel listing restriction)
