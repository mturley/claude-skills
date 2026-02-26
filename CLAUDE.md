# Claude Code Instructions

This is a **public repository**. Before making any commit, review the staged changes for:

- API keys, tokens, or credentials
- Personal information (emails, usernames tied to internal systems)
- References to private repos or proprietary systems
- Details of specific Jira tickets (summaries, descriptions, comments)

**Acceptable to share:**
- Red Hat Jira URLs, project IDs, and field IDs (this is public infrastructure)
- Jira field names and custom field identifiers
- Sprint and team naming conventions

If you find anything that looks like it shouldn't be public, **stop and describe it to the user** before committing. Ask them to confirm whether the content is safe to publish.

# Skill Maintenance

When modifying skills:
- Check the skill's README.md and update it if the changes affect usage, installation, or behavior
- Keep the root README.md in sync (skill descriptions, links)

When creating new skills:
- Create a README.md in the skill directory explaining usage and installation
- Add a reference to the new skill in the root README.md under "## Skills"
- Commit and push all changes
