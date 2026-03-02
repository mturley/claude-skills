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

To make this documentation available to Claude in all sessions:

### Step 1: Symlink the directory

```bash
ln -s ~/git/claude-skills/.mcp-usage ~/.claude/skills/.mcp-usage
```

This makes the files physically accessible. Do this alongside symlinking individual skills.

### Step 2: Add a generic MCP reference to your global CLAUDE.md

Create or edit `~/.claude/CLAUDE.md` and add this section:

```markdown
# MCP Server Operations

Before using any MCP server tools, check `~/.claude/skills/.mcp-usage/` for a corresponding
documentation file. These files contain server-specific information like custom field IDs,
format requirements, and gotchas.
```

This single instruction works for **all MCP servers** (Jira, Puppeteer, etc.). Claude will check
the `.mcp-usage/` directory for relevant documentation when using any MCP.

**Why this is needed:** The symlink makes files accessible, but Claude won't proactively check them
without explicit instructions in CLAUDE.md. Skills can reference these files directly, but for
Claude to use this documentation outside of skill contexts (e.g., when you ask Jira questions directly),
you need this reference.

## Adding New MCP Documentation

When documenting a new MCP server:

1. Create `[mcp-name].md` in this directory (lowercase, matching the MCP server name)
2. Follow the standard format with sections:
   - **Quick Reference** - Most commonly needed information
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
