---
name: milestones
description: Show upcoming RHOAI release milestones from Product Pages, with filtering by date range or version
---

# RHOAI Milestones

Show upcoming RHOAI release milestones from the Product Pages MCP server.

**Technical Reference:** For entity patterns, deduplication gotchas, and query patterns, see [`../.context/productpages-mcp.md`](../.context/productpages-mcp.md)

## Arguments

`$ARGUMENTS` — Optional, space-separated. Supports:

- **No arguments**: Major releases only, next 3 months
- **Date range**: `6 months`, `this year`, `through december`, `2 months`, `1 year`, etc.
- **Single version**: `3.5` — show all milestones for that version (EA1, EA2, GA)
- **Version range**: `through 3.6` — show milestones from now through end of that version
- **`all` flag**: Include z-stream/patch releases (can combine with any of the above)

Examples:
- `/milestones` — major releases, next 3 months
- `/milestones 6 months` — major releases, next 6 months
- `/milestones 3.5` — all 3.5 milestones
- `/milestones through 3.6` — everything through 3.6 GA
- `/milestones all` — all releases including patches, next 3 months
- `/milestones all through 3.6` — everything including patches, through 3.6 GA

## Instructions

### Step 0: Check for Help

If `$ARGUMENTS` is `help`, output the following and stop:

```
/milestones — RHOAI release milestones from Product Pages

Usage:
  /milestones                     Major releases, next 3 months
  /milestones 6 months            Major releases, next 6 months
  /milestones this year           Major releases through end of year
  /milestones 3.5                 All 3.5 milestones (EA1, EA2, GA)
  /milestones through 3.6         Major milestones through 3.6 GA
  /milestones all                 All releases (including patches), next 3 months
  /milestones all 6 months        All releases, next 6 months
  /milestones all through 3.6     All releases through 3.6 GA

Options:
  all              Include z-stream/patch releases (adds ⭐ column for major)
  <version>        Show milestones for a specific version (e.g. 3.5)
  through <ver>    Show milestones through a version (e.g. through 3.6)
  <time range>     Set date range (e.g. 6 months, this year, 2 weeks)
  help             Show this help message
```

### Step 1: Parse Arguments

Parse `$ARGUMENTS` to determine:

1. **`include_minor`**: whether `all` is present (remove it from remaining args)
2. **Mode** from remaining args:
   - Empty → **date mode**, end date = today + 3 months
   - Matches a version pattern like `3.5` → **single version mode**
   - Starts with `through` followed by a version like `through 3.6` → **version range mode**
   - Otherwise → **date mode**, interpret as relative time (e.g. `6 months`, `this year`, `1 year`)

For date mode, compute the end date:
- `N months` → today + N months
- `N weeks` → today + N weeks
- `this year` → December 31 of current year
- `this quarter` → end of current quarter
- Other natural language → interpret reasonably

### Step 2: Fetch Milestones

Read `../.context/productpages-mcp.md` for reference. RHOAI product entity ID is `152`.

**For single version mode** (e.g. `3.5`):

1. Search for the `.z` entity: `search_entities(q="RHOAI 3.5", kind="release")`
2. Find the entity with shortname `rhoai-3.5.z`
3. Call `browse_schedule(entity_id=<id>)`
4. Filter out level-0 grouping tasks (keep only `level >= 1`)
5. Skip to Step 3

**For date mode or version range mode:**

Call `list_schedule_tasks` with:
- `parent_id__in=[152]`
- `date_finish__gte=<today>` (always — don't show past milestones)
- `date_finish__lte=<end_date>` (for date mode only)
- `flags=["keydate"]`
- `ordering=["date_finish"]`

For **version range mode** (e.g. `through 3.6`): don't set `date_finish__lte`. Instead, you'll filter by version in Step 3.

### Step 3: Format and Output

Pipe the raw JSON result from the MCP call through `format-milestones.py` (in the skill's base directory) and output the result verbatim.

The script handles deduplication, major/minor classification, version filtering, and markdown table rendering.

**Build the command based on the parsed arguments:**

```bash
echo '<raw JSON from MCP tool result>' | python3 <base_dir>/format-milestones.py \
  --today <today YYYY-MM-DD> \
  [--end-date <end YYYY-MM-DD>] \
  [--include-minor] \
  [--through <version>] \
  [--version <version>]
```

Flags:
- `--today`: always required (today's date)
- `--end-date`: for date mode, the computed end date
- `--include-minor`: if `all` was in the arguments
- `--through VERSION`: for version range mode
- `--version VERSION`: for single version mode

Output the script's stdout as-is — it contains the summary line and markdown table.
