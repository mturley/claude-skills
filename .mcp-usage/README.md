# MCP Usage Reference

Documentation for using Model Context Protocol (MCP) servers with Claude Code. This is a shared reference for team members configuring and using MCPs.

## Available References

- **[Jira MCP](jira.md)** - Field IDs, custom field formats, search patterns, and troubleshooting for RHOAIENG project
- **[Puppeteer MCP](puppeteer.md)** - Browser automation patterns (placeholder)

## What This Directory Contains

This directory contains **usage patterns** for MCP servers - things like:
- Field IDs and custom field formats
- Known limitations and workarounds
- Common gotchas and troubleshooting
- Usage patterns specific to our team's workflows

**Note:** Setup/configuration instructions are environment-specific and should be kept in personal notes (e.g., `~/Documents/md-redhat/AI Tool Use/`).

## Installation

To make this documentation accessible to Claude in all sessions, symlink the entire claude-skills repo to `~/.claude/skills/`:

```bash
ln -s ~/git/claude-skills ~/.claude/skills
```

This makes the `.mcp-usage` directory (and all skills) accessible at `~/.claude/skills/.mcp-usage`.

## Adding New MCP Documentation

When documenting a new MCP server:

1. Create `[mcp-name].md` in this directory (lowercase, matching the MCP server name)
2. Follow the standard format with sections:
   - **Quick Reference** - Most commonly needed information
   - **Available Tools** - List of MCP tools with descriptions
   - **Custom Fields & Configuration** - Field IDs, format requirements
   - **Usage Patterns** - How to effectively use this MCP
   - **Known Limitations & Workarounds** - Gotchas discovered through usage
   - **Troubleshooting** - Common errors and solutions
3. Include only usage information (not setup/authentication details)
4. Verify no credentials or sensitive information are included (public repo)
5. Update this README to link to the new file

## Public Repository Safety

This is a **public repository**. Include only:
- ✅ Field IDs and custom field names
- ✅ Format requirements and patterns
- ✅ API limitations and workarounds
- ✅ Public project identifiers

Do NOT include:
- ❌ API tokens or credentials
- ❌ Specific ticket details (summaries, descriptions)
- ❌ Internal documentation links
- ❌ Team-specific sprint names or internal processes (use generic examples)
