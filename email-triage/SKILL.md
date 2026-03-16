# Email Triage

Scan unread Gmail for important emails that need attention, filtering out noise from mailing lists, bots, and calendar invitations.

**Requires:** Google Workspace MCP server

## Instructions

### Phase 1: Fetch Unread Emails

Run these searches in parallel to cast a wide net:

1. **Directly addressed, recent** (last 30 days):
   ```
   is:unread to:me -from:noreply -from:no-reply -from:notifications@ category:personal
   ```
   Max 100 results.

2. **Action-required keywords** (last 90 days):
   ```
   is:unread to:me subject:(action OR review OR approve OR sign OR deadline OR urgent OR ASAP OR reminder OR complete OR required OR overdue)
   ```
   Max 50 results.

3. **Important unread from humans** (last 30 days):
   ```
   is:unread is:important -from:jira -from:noreply -from:no-reply -from:notifications@ -from:notification@ -from:gemini-notes@ -from:hello@udemybusiness
   ```
   Max 100 results.

4. **Mentions by name** (last 30 days):
   Search for the user's first name in the body/subject to catch @-mentions in Jira, GitHub, or mailing list replies:
   ```
   is:unread "mentioned you" OR "@<first name>"
   ```
   Max 50 results.

### Phase 2: Deduplicate and Filter

1. Deduplicate results by message ID across all searches.
2. **Filter out noise** — remove emails matching these patterns:
   - Calendar invitations and cancellations (subjects starting with "Invitation:", "Updated invitation:", "Canceled event:", or from Google Calendar)
   - Automated meeting notes (from `gemini-notes@google.com`)
   - Bot/CI notifications (from addresses containing `noreply`, `no-reply`, `bot`, `notifications@`) — **unless** the subject contains action-required keywords
   - Marketing/promotional emails (Udemy, newsletters, etc.)
   - Mailing list traffic where the user is not directly addressed or mentioned — **unless** the subject contains action-required keywords
   - Old Jira status-change notifications (transitions, field updates) — **keep** Jira notifications where the user is mentioned or assigned
   - Slack digest emails
   - Expired deadlines from more than 6 months ago (benefits enrollment, token expiration, etc.) — flag these for bulk archival instead

3. **Keep** emails that match any of these signals:
   - User is directly mentioned by name (e.g., "@Mike" in a Jira comment)
   - User is the sole or primary recipient (not a large CC list or mailing list)
   - Subject contains compliance/training deadlines
   - From a person (not a bot) and marked Important by Gmail
   - Contains a direct question or request to the user

### Phase 3: Categorize by Urgency

Sort the remaining emails into these categories:

**Needs Action NOW** — Items with approaching or imminent deadlines, direct questions to the user, compliance/training requirements, or security notices. Include the deadline date if known.

**Should Respond Soon** — Direct messages from colleagues, mentions in Jira/GitHub where input is requested, meeting-related requests. No hard deadline but social expectation of timely response.

**Overdue / Check Status** — Action items where the deadline has already passed. Note how old they are. The user may need to check whether these are still relevant or have been resolved through other channels.

**FYI / Can Safely Archive** — Emails that were caught by the search but don't actually need action. Expired reminders, resolved threads, informational broadcasts. Suggest bulk archiving these.

### Phase 4: Present the Report

Format the output as a clear, scannable report:

```
## Email Triage Report — <today's date>

**<N> important emails found** out of <M> unread scanned

### Needs Action NOW
- **<Subject>** — from <Sender>, <date>
  <One-line summary of what's needed and any deadline>

### Should Respond Soon
- ...

### Overdue / Check Status
- ...

### FYI / Can Safely Archive (<count> emails)
<Brief summary of what's in this bucket, not individual items>
```

**Formatting rules:**
- Bold the subject line of each email
- Include the sender's name (not full email address) and relative date (e.g., "3 days ago", "2 weeks ago")
- For items with deadlines, include the deadline prominently
- Keep summaries to one line per email — enough to decide whether to act on it
- For the "Needs Action NOW" section, order by deadline (soonest first)
- For the "FYI / Can Safely Archive" section, just summarize the types of emails (e.g., "12 expired calendar invitations, 5 old mailing list threads") rather than listing each one
