# Recommended Review

Load the PR Reviews Dashboard from http://localhost:5173/, wait for it to finish loading, and summarize the recommended actions.

**Prerequisite:** The [pr-reviews-dashboard](https://github.com/mturley/pr-reviews-dashboard) app must be running locally at http://localhost:5173/ before invoking this skill. If the page fails to load, tell the user to start the app first.

## Instructions

### Step 1: Launch browser and load the page

1. Launch a Puppeteer browser instance (headless, 1366x900 viewport).
2. Create a new page (`pageId: "reviews-dashboard"`).
3. Navigate to `http://localhost:5173/` with `waitUntil: "networkidle2"`.

### Step 2: Wait for loading to complete

The dashboard shows a progressive loading indicator that disappears when all data is loaded. Wait for loading to finish:

1. Wait up to 60 seconds for the loading indicator to disappear. Use `puppeteer_evaluate` to poll for completion:
   ```js
   // Loading is complete when there is no element with text "Loading:" visible
   !document.body.innerText.includes('Loading:')
   ```
   Poll every 3 seconds. If it doesn't complete within 60 seconds, take a screenshot and report the current state to the user.

### Step 3: Expand recommended actions

1. Check if there is a "Show N more" button/link in the recommended actions section. If so, click it using `puppeteer_click` with selector `text/Show`.
2. Wait 1 second for the UI to update.

### Step 4: Extract and summarize

1. Use `puppeteer_get_text` on `body` to get the full page text.
2. Take a screenshot for reference.
3. Parse the recommended actions from the text. Each action has:
   - Action type (e.g., "Re-review PR", "Review PR")
   - Review status (e.g., "My Re-review Needed", "Needs First Review", "Team Re-review Needed", "Needs Additional Review")
   - PR number, title, and repo
   - Author
   - Priority (if linked to Jira)
   - Jira issue key and summary (if linked)

4. Present a summary table of the recommended actions, ordered by priority. Include the action type, PR link, repo, author, and why action is needed.

5. Render Jira issue keys as markdown links to `https://issues.redhat.com/browse/{key}` (e.g., `[RHOAIENG-46284](https://issues.redhat.com/browse/RHOAIENG-46284)`).

6. Offer to help with the first recommended action (e.g., "Would you like me to run `/review` on that PR?").

### Step 5: Clean up

Close the browser with `puppeteer_close_browser`.
