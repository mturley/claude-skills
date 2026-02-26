# Create Jira

Create a Jira issue in the RHOAIENG project for the RHOAI Dashboard team (Model Registry / Model Catalog areas).

## Arguments

- `$ARGUMENTS` - Optional issue type: `bug`, `task`, or `story`

## Instructions

1. **Determine the issue type** (Bug, Task, or Story):
   - If the user passed an argument (e.g., `/create-jira bug`), use that type
   - Otherwise, ask the user for the issue type

2. **Gather context about the issue**:
   - Review the conversation history for any context the user has already provided about the issue (bug description, feature request, task details, etc.)
   - If no context exists: Ask the user to describe the issue at a high level

3. **Research the codebase**:
   - Based on the user's description, search for relevant code (use Grep, Glob, Read tools)
   - Try to identify the root cause or the area where the problem likely exists
   - For bugs: Look for the specific code paths involved
   - For tasks/stories: Identify the files and components that would need to be modified
   - Use findings to enrich the issue description with technical details and file references
   - When referencing files, include GitHub links (see "File References" section below)

4. **Ask the user for the area** (one of) - if not already clear from context:
   - Model Catalog only - use label `dashboard-area-model-catalog`
   - Model Registry only - use label `dashboard-area-model-registry`
   - Both Model Catalog and Model Registry - use both labels

5. **Present the drafted title and description** for user approval. Allow them to refine it.
   - Track whether the user made significant changes to the AI-suggested description

6. **Ask the user for Priority** (one of: Blocker, Critical, Major, Normal, Minor, Undefined)

7. **If the issue type is Bug, ask for Severity** (customfield_12316142)

8. **Create the issue** using jira_createIssue with these properties:
   - Project ID: `12340620` (RHOAIENG) - must ALSO be included in customFields as `"project": {"id": "12340620"}`
   - Component: AI Core Dashboard (add via customFields)
   - Team (customfield_12313240): `"4158"` (RHOAI Dashboard) - note: must be a string, not an object
   - Labels: Based on area selection
   - Priority: Based on user selection (use priority object with id)
   - Severity: If Bug, based on user selection
   - Issue Type IDs:
     - Bug: `1`
     - Task: `3`
     - Story: `17`
   - Description: Use the user-approved description, formatted according to the templates below

9. **After creating the issue**, provide the user with:
   - The issue key (e.g., RHOAIENG-XXXXX)
   - A link to the issue: `https://issues.redhat.com/browse/{issueKey}`

10. **Ask if they want to add it to a sprint**. If yes:
    - Search for Green sprints using the technique described in "Finding Green Sprints" below
    - Use the active Green sprint for "current sprint" or the next future Green sprint for "next sprint"
    - Update the issue's sprint field (customfield_12310940) with the sprint ID (integer)
    - Transition the issue from "New" to "Backlog" using jira_getTransitions to find the transition ID, then jira_transitionIssue to perform the transition

## Finding Green Sprints

The Jira sprint field does NOT support text search operators like `~`. To find Green sprints:

1. **For current sprint**: Search for issues in open sprints with the model-registry label:
   ```
   project = RHOAIENG AND sprint in openSprints() AND labels = "dashboard-area-model-registry" ORDER BY created DESC
   ```

2. **For next sprint**: Search for issues in future sprints:
   ```
   project = RHOAIENG AND component = "AI Core Dashboard" AND sprint in futureSprints() ORDER BY created DESC
   ```

3. **Parse the sprint field** from results. The `customfield_12310940` field contains sprint data as strings like:
   ```
   com.atlassian.greenhopper.service.sprint.Sprint@...[id=82844,rapidViewId=18687,state=FUTURE,name=Dashboard - Green-35,...]
   ```

4. **Filter for "Green" sprints only**. Multiple scrum teams share this board with different sprint names:
   - Green sprints: `Dashboard - Green - N` or `Dashboard - Green-N` (Model Registry/Catalog team)
   - Razzmatazz sprints: `Dashboard - Razzmatazz - N` (different team)
   - Monarch sprints: `Dashboard - Monarch-N` (different team)

   **IMPORTANT**: Only use sprints with "Green" in the name. Never select Razzmatazz, Monarch, or other sprint names.

5. **Extract the sprint ID** (e.g., `82844`) from the string and use it as an integer when updating the issue.

## Priority IDs
Use `{"id": "<id>"}` format for priority field.
- Blocker: 1
- Critical: 2
- Major: 3
- Normal: 10200
- Minor: 4
- Undefined: 10300

## Severity Values (Bugs only)
Use `{"value": "<value>"}` format for customfield_12316142. Do NOT use `{"name": "..."}` - it will fail.
- Urgent
- High
- Moderate
- Low

## Description Templates

When drafting descriptions, use both the user's context AND findings from the codebase research to fill in the relevant sections. Include specific file paths, function names, and technical details discovered during research. Present the draft to the user for approval before creating the issue.

**AI Disclaimer**: Add a note at the very top of the description (before any other content):
- If the user accepted the AI-generated description with no or minor changes: `_This issue description was generated by AI._`
- If the user made significant changes to the AI-suggested description: `_This issue description was generated in part by AI._`
- For bugs, append to the disclaimer: `_Assertions about root cause and suggested fix may be inaccurate._`

For Bugs, use this format (fill in sections based on user context, leave placeholders for unknown info):
```
h3. Description of problem
[Draft based on user context]

h3. Prerequisites (if any, like setup, operators/versions)
[If known from context, otherwise leave as TBD]

h3. Steps to Reproduce
# [Draft steps based on context]

h3. Actual results
[Draft based on context]

h3. Expected results
[Draft based on context]

h3. Reproducibility (Always/Intermittent/Only Once)
[If known, otherwise leave as TBD]

h3. Found in what build
[If known, otherwise leave as TBD]

h3. Describe any workarounds
[If known, otherwise "None known"]

h3. Additional information
[Any other relevant context]
```

For Tasks/Stories, use this format:
```
h3. Description
[Draft based on user context - what needs to be done and why]

h3. Acceptance Criteria
* [Draft criteria based on context]
```

## File References

When referencing files in the issue description, include GitHub links:
1. Determine the GitHub repo URL by running `git remote get-url upstream` and converting it to HTTPS format
2. Link to files on the `main` branch using Jira Wiki Markup syntax:
   - Basic file link: `[filename|https://github.com/OWNER/REPO/blob/main/path/to/file.ts]`
   - Specific line: `[filename:L42|https://github.com/OWNER/REPO/blob/main/path/to/file.ts#L42]`
   - Line range: `[filename:L42-L50|https://github.com/OWNER/REPO/blob/main/path/to/file.ts#L42-L50]`

Note: Use Jira Wiki Markup link syntax `[text|url]` not Markdown syntax.

## Important Notes
- If using Jira MCP tools encounters issues, stop and ask the user how to proceed
- Always show the created issue link to the user
