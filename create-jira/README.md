# /create-jira

This skill helps open detailed Jira issues by gathering context and investigating code, properly labeling and triaging them. It is specific to Green scrum's current feature areas (model catalog and registry), but I plan to generalize it.

## Installation

1. Set up a Jira MCP server. I use `@atlassian-dc-mcp/jira`, which is specific to Jira Datacenter, but we will need to reconfigure things when we move to Jira Cloud. The skill may also need adjustments at that point because it uses specific field ids and query behavior.
    * You can just ask Claude "Help me set up the @atlassian-dc-mcp/jira MCP server using JIRA_HOST=issues.redhat.com"

2. Place the skill at `~/.claude/skills/create-jira/SKILL.md`.

## Prerequisites

- Must be in a git repository with an `upstream` remote pointing to GitHub (used for generating file links in issue descriptions)

## Usage

You can use it in 2 ways - with or without prior context. I recommend using Claude Opus if you want the skill to deeply investigate the code to find a root cause. In either case, you will get an issue description that fills in our template (for bugs), with an "additional info" section identifying the possible root cause and recommending a solution. It will include a disclaimer that these were generated with AI and may be inaccurate.

### Without prior context

1. At the start of your claude session, run `/create-jira [bug|task|story]`.
2. Claude will ask you to describe the issue from a high level. In this message, give Claude what it needs to find as much context as possible - but you can be indirect about it by using links, screenshots, and pointers to code.

**Examples:**

> We're not rendering errors properly when fetching model catalog performance artifacts. I think this bug was caused by changes to the CatalogModelCard component in <pr-url>. There are details about the original implementation of this fetch in the Jira story <jira-url>. Here is a screenshot of how the error looks today, and here is a screenshot of the mockup it should look like. Also, here is a screenshot of a slack thread discussing the bug. [pasting 3 screenshots along with the prompt]

> Look at the review comment <pr-comment-url>. It is out of scope of the PR and needs a followup issue.

> Look at this Jira issue <jira-url>. It is too large and should be broken into multiple issues. Find the relevant code and think about how we could break up the work to be parallelized. For more context, look at the comments on the issue and look at this slack thread [screenshot].
  
3. Claude will look at all the context you gave it and investigate the code locally to find a likely root cause. It will draft a title and description for the issue, and identify what feature area labels should be on the issue. It will ask you to review these and give any feedback, what the priority and severity should be (for bugs), and whether you want to add it to a sprint (the current or next sprint).
  
4. Claude will create the issue for you and give you the link, and if you asked it to put the issue in a sprint it will do so and transition the issue from New to Backlog.
  
### With prior context
  
If you are in a Claude session and you have identified something that needs a followup Jira issue (maybe you're reviewing a PR or you're working on another issue and you find a bug that's out of scope), you can use that existing context as input for this skill.

1. Run the skill with short additional input to identify what part of the conversation is relevant. You can use Shift+Enter to make a new line for giving the skill extra input separate from its arguments. For example:

> /create-jira bug
> The pagination bug you found needs a separate followup issue.
  
2. Claude will further investigate the code locally, then draft a title and description for the issue based on prior context in the conversation, as well as identify what feature area labels should be on the issue. It will ask you to review these and give any feedback, what the priority and severity should be (for bugs), and whether you want to add it to a sprint (the current or next sprint).
  
3. Claude will create the issue for you and give you the link, and if you asked it to put the issue in a sprint it will do so and transition the issue from New to Backlog.
   
## Possible improvements
   
It would be great if the skill could look up our scrums' feature areas and understand how to properly use those labels and identify which scrum's sprints to look for based on that context. We could do this by giving it access to our scrum-specific Jira filters, or directing it to our Confluence pages.