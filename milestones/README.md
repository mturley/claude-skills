# /milestones

Shows upcoming RHOAI release milestones from the Product Pages MCP server.

## Requirements

- Product Pages MCP server configured and authenticated

## Usage

```
/milestones                    # Major releases, next 3 months
/milestones 6 months           # Major releases, next 6 months
/milestones this year          # Major releases through end of year
/milestones 3.5                # All 3.5 milestones (EA1, EA2, GA)
/milestones through 3.6        # Everything through 3.6 GA
/milestones all                # All releases including patches, next 3 months
/milestones all through 3.6    # Everything including patches, through 3.6 GA
```

## Output

Markdown table with milestone dates, emoji markers for freeze milestones (🧊), and when showing all releases, a ⭐ column to distinguish major from patch releases.

## How It Works

The skill queries the Product Pages MCP server (`mcp__productpages__*` tools) for RHOAI schedule data, then pipes the raw JSON through `format-milestones.py` which handles deduplication, major/minor classification, version filtering, and markdown table rendering. This keeps the LLM focused on argument parsing and MCP calls while the deterministic logic runs instantly in Python.
