---
name: slack-status
description: Use when the user wants to see recent Zaffre scrum status updates from the wg-dashboard-zaffre Slack channel, or when they want to monitor the latest status thread for new replies.
---

# /slack-status — Zaffre Scrum Status Threads

Fetch, summarize, and optionally watch the two most recent status sync threads from the `#wg-dashboard-zaffre` Slack channel.

**Technical Reference:** See [`../.context/slack-mcp.md`](../.context/slack-mcp.md) for channel IDs and Slack MCP quirks.

## Constants

- **Channel ID:** `C069KSM8T9N` (`#wg-dashboard-zaffre`)
- **Status thread trigger text:** `Slack scrum sync!`
- **Watch interval:** 20 minutes

## Instructions

### Step 1: Find the Two Most Recent Status Threads

Call `mcp__slack__get_channel_history` with `channel_id=C069KSM8T9N` and `limit=200`.

Scan the result for messages where **@Slackbot** sent a message containing `Slack scrum sync!`. These are the status reminder threads. Collect their `thread_ts` (timestamp) values.

Sort them descending by timestamp. Take the **two most recent**.

If fewer than 2 are found, note how many were found and proceed with what's available.

### Step 2: Fetch Thread Replies

For each of the two status thread timestamps, call `mcp__slack__get_thread` with the channel ID and that `thread_ts`.

Collect all replies (messages after the initial Slackbot reminder).

### Step 3: Summarize Both Threads

Present a summary of each thread in **chronological order** (oldest first, most recent last). Format:

```
## Status Sync — [human-readable date from thread_ts]

**Participants:** [list of names who replied]

**Summary:**
- [Person]: [what they said they were working on, blockers, progress]
- [Person]: [their status]
...

**Key items:**
- [Notable blockers, decisions, PRs mentioned, or action items across the thread]
```

For the summary:
- Condense each person's replies into a few bullet points
- Flag blockers explicitly
- Include PR/Jira links when they appear in the message
- If a long back-and-forth technical discussion happened in the thread, summarize the resolution or open question

### Step 4: Offer to Watch

After presenting both summaries, ask the user:

> Would you like me to watch the latest status thread (`[date of most recent]`) for new replies? I'll check every 20 minutes and summarize any new activity when you send a prompt.

Wait for the user's response.

### Step 5: If User Says Yes — Start Watching

**Record the watch state:**
- Store the latest thread's `thread_ts` (call it `$WATCH_TS`) and the last message timestamp seen (call it `$LAST_SEEN_TS`) — set this to the timestamp of the last reply in the thread at the time the user agreed.
- Store the channel ID: `C069KSM8T9N`

**Schedule the watcher using CronCreate:**

```
Schedule a cron job to fire every 20 minutes (e.g. "*/20 * * * *", recurring: true).
Prompt: "Check #wg-dashboard-zaffre status thread for new replies and summarize them. Channel: C069KSM8T9N, thread_ts: $WATCH_TS, last_seen_ts: $LAST_SEEN_TS"
```

Tell the user:
> Watching the status thread. I'll check every 20 minutes and summarize new replies when you send a prompt. Say "stop watching" to cancel.

### Step 6: While Watching — On Each User Prompt

When the user sends any prompt while a watch cron is active:

1. Call `mcp__slack__get_thread` for the watched thread
2. Filter replies to only those with timestamp > `$LAST_SEEN_TS`
3. If there are new replies:
   - Summarize them (same format as Step 3 but for new replies only)
   - Update `$LAST_SEEN_TS` to the most recent reply timestamp
4. If no new replies: briefly note "No new replies in the status thread since last check."

Then continue handling whatever the user actually asked about.

### Step 7: Stop Watching

If the user says "stop watching", "unwatch", "cancel watch", or similar:
1. List active cron jobs with CronList
2. Delete the status-thread watcher cron with CronDelete
3. Confirm: "Stopped watching the status thread."

## Notes

- The watch cron prompt tells a future Claude invocation what thread to watch and where it left off — include those values literally in the prompt text.
- Status threads fire on a recurring schedule (weekdays); the skill will find new ones automatically each time `/slack-status` is run fresh.
- The Slack MCP enterprise restriction means you can't look up channels by name — always use the hardcoded channel ID.
