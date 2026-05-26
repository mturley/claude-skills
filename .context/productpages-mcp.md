# Product Pages MCP Reference

Technical reference for using the Product Pages MCP server with RHOAI.

## Server Configuration

**Server:** Product Pages MCP
**MCP server name:** `productpages` (tools are `mcp__productpages__*`)
**Purpose:** Red Hat's internal system for product schedules, roadmaps, milestones, and program sourcing information (people, roles, contacts)

## RHOAI Entity Structure

**RHOAI product entity:** ID `152`, kind `product`, shortname `rhoai`
- Found via `search_entities(q="RHOAI", kind="product")`

### Release Entity Naming Convention

RHOAI has **multiple release entities per version**, which causes duplicate results:

| Pattern | Example | Notes |
|---------|---------|-------|
| `rhoai-X.Y` | `rhoai-3.5` (ID 3195) | Named GA release |
| `rhoai-X.Y.z` | `rhoai-3.5.z` (ID 3351) | **Consolidated z-stream schedule — has the most complete data** |
| `rhoai-X.Y.EAn` | `rhoai-3.5.EA1` | EA release entities |
| `rhoai-X.Y.N` | `rhoai-3.3.4` | Specific patch releases |

**Always prefer the `.z` entity** when you need the full schedule for a version. It contains all EA and GA milestones in one place.

## Deduplication Gotchas

The API returns the **same logical milestone from multiple entities**. For example, "3.5 RHOAI Code Freeze" appears under both `rhoai-3.5` and `rhoai-3.5.z`.

When deduplicating:
- Group by (date, milestone name) and keep only one entry per logical milestone
- **Prefer non-draft, roadmap-flagged entries** from the `.z` entity
- Draft entries (`"draft": true`) may have outdated dates
- Skip level-0 tasks from `browse_schedule` — these are grouping containers (date ranges like "3.5 Red Hat OpenShift AI"), not actual milestones

## Milestone Naming

RHOAI does **not** use the global milestone definitions from `list_schedule_milestones`. For example, "Development Freeze" (milestone ID 6) returns no results for RHOAI.

Instead, milestones are embedded in task names:
- `"3.5 RHOAI Code Freeze"`
- `"3.5 RHOAI Feature Freeze"`
- `"3.5 EA1 RHOAI RELEASE"`
- `"3.5 RHOAI GA"`
- `"3.5 Planning Freeze"`
- `"3.5 RHOAI Initial RC"`
- `"3.5 CCS content published"`

Search with `q="freeze"` or `q="code freeze"` to find freeze milestones.

## Best Query Patterns

### "What's next?" — upcoming milestones across all releases

```
list_schedule_tasks(
  parent_id__in=[152],
  date_finish__gte="<today>",
  ordering=["date_finish"],
  flags=["keydate"]
)
```

### Full schedule for a specific version

```
browse_schedule(entity_id=<.z entity ID>)
```

Use the `.z` entity ID (e.g. 3351 for rhoai-3.5.z). Returns a hierarchical tree with EA1, EA2, and GA phases. Filter out level-0 grouping tasks.

### Search by keyword

```
list_schedule_tasks(
  parent_id__in=[152],
  q="freeze",
  date_finish__gte="<today>",
  ordering=["date_finish"]
)
```

## Filtering Tips

| Flag | Effect |
|------|--------|
| `flags=["keydate"]` | Filters to actual milestones (excludes date-range spans) |
| `flags=["roadmap"]` | Further filters to published/official milestones |
| `flags=["keydate", "roadmap"]` with default AND mode | Only roadmap keydates |

## Deduplication Algorithm

The API returns the same logical milestone from multiple release entities. When querying RHOAI milestones via `list_schedule_tasks`, always deduplicate:

1. Group results by (`date_finish`, milestone name with version prefix stripped)
2. For each group, keep the entry that is:
   - Non-draft (`draft: false`) preferred over draft
   - Has `roadmap` flag preferred over entries without it
   - From a `.z` entity preferred over non-`.z`
3. Drop any remaining duplicates

## Major vs Minor (Patch) Classification

A milestone is **minor** (z-stream/patch) if its name starts with a patch version pattern — a version with 3+ numeric segments like `3.3.4`, `3.4.1`, `2.25.7`, `2.25.8`.

A milestone is **major** if it is NOT minor — names like `3.5 RHOAI Code Freeze`, `3.5 EA1 RHOAI RELEASE`, `3.6 RHOAI GA`.

**By entity shortname:**
- Major: `rhoai-X.Y`, `rhoai-X.Y.z`, `rhoai-X.Y.EAn`
- Patch: `rhoai-X.Y.N` (e.g. `rhoai-3.3.4`)
