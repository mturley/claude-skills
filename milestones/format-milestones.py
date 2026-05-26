#!/usr/bin/env python3
"""Format RHOAI milestones from Product Pages API JSON into a markdown table.

Reads the raw `data` array from list_schedule_tasks or browse_schedule on stdin.
Handles deduplication, major/minor classification, version filtering, and rendering.

Uses only Python stdlib. No pip dependencies.
"""

import argparse
import json
import re
import sys
from datetime import datetime


def parse_args():
    p = argparse.ArgumentParser(description="Format RHOAI milestones as markdown")
    p.add_argument("--include-minor", action="store_true",
                    help="Include patch/z-stream milestones (adds star column)")
    p.add_argument("--through", dest="through_version", metavar="VERSION",
                    help="Version range ceiling (e.g. 3.6)")
    p.add_argument("--version", dest="single_version", metavar="VERSION",
                    help="Single version mode (e.g. 3.5)")
    p.add_argument("--today", required=True, help="Today's date (YYYY-MM-DD)")
    p.add_argument("--end-date", dest="end_date",
                    help="End date for summary line (YYYY-MM-DD, date mode only)")
    return p.parse_args()


def read_input():
    raw = sys.stdin.read()
    if not raw.strip():
        print("Error: No input on stdin.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def normalize_name(name):
    """Strip version prefix for dedup grouping. '3.5 RHOAI GA' -> 'RHOAI GA'."""
    return re.sub(r'^[\d.]+\s*(EA\d+\s*)?', '', name).strip()


def is_patch_milestone(name):
    """A milestone is minor/patch if its name starts with a 3+-segment version (e.g. 3.3.4)."""
    return bool(re.match(r'^\d+\.\d+\.\d+', name))


def is_z_entity(shortname):
    return shortname and shortname.endswith('.z')


def dedup_score(task):
    """Higher score = preferred entry during deduplication."""
    score = 0
    if not task.get("draft", False):
        score += 4
    if "roadmap" in task.get("flags", []):
        score += 2
    shortname = task.get("entity", {}).get("shortname", "")
    if is_z_entity(shortname):
        score += 1
    return score


def deduplicate(tasks):
    groups = {}
    for t in tasks:
        key = t["name"]
        if key not in groups or dedup_score(t) > dedup_score(groups[key]):
            groups[key] = t
    return sorted(groups.values(), key=lambda t: (t["date_finish"], t["name"]))


def is_date_range_task(task):
    """Filter out grouping/container tasks that span long date ranges."""
    start = task.get("date_start", "")
    finish = task.get("date_finish", "")
    if not start or not finish:
        return False
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        f = datetime.strptime(finish, "%Y-%m-%d")
        return (f - s).days > 14
    except ValueError:
        return False


def extract_version(name):
    """Extract the version prefix from a milestone name (e.g. '3.5' from '3.5 RHOAI GA')."""
    m = re.match(r'^(\d+\.\d+(?:\.\d+)*)', name)
    return m.group(1) if m else None


def version_tuple(v):
    """Convert version string to tuple for comparison. '3.5' -> (3, 5)."""
    return tuple(int(x) for x in v.split('.'))


def version_at_or_below(v, ceiling):
    """Check if version v is at or below the ceiling (comparing major.minor only)."""
    vt = version_tuple(v)
    ct = version_tuple(ceiling)
    return vt[:2] <= ct[:2]


def filter_through_version(tasks, through_version, include_minor):
    """Keep milestones whose version is at or below the target."""
    result = []
    for t in tasks:
        v = extract_version(t["name"])
        if not v:
            continue
        if not version_at_or_below(v, through_version):
            continue
        if not include_minor and is_patch_milestone(t["name"]):
            continue
        result.append(t)
    return result


def format_date_short(date_str):
    """Format YYYY-MM-DD as 'Mon D' (e.g. 'Jun 17')."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b ") + str(dt.day)


def format_date_range(start, finish):
    """Format a date or date range as bold markdown."""
    if start == finish or not start:
        return f"**{format_date_short(finish)}**"
    s = datetime.strptime(start, "%Y-%m-%d")
    f = datetime.strptime(finish, "%Y-%m-%d")
    if s.month == f.month and s.year == f.year:
        return f"**{format_date_short(start)}–{f.day}**"
    return f"**{format_date_short(start)} – {format_date_short(finish)}**"


def format_milestone_name(name):
    """Apply emoji decorations to milestone name."""
    result = name
    if "RHOAI GA" in name or "RHOAI RELEASE" in name:
        result = f"**{result}**"
    if "Code Freeze" in name or "Feature Freeze" in name:
        result = f"\U0001f9ca {result}"
    return result


def build_summary(args, count):
    """Generate the one-line summary header."""
    today_str = format_date_short(args.today)
    if args.single_version:
        label = f"RHOAI {args.single_version} milestones"
        if args.include_minor:
            label += " (all releases)"
        return f"{label}:"
    if args.through_version:
        label = f"RHOAI milestones through {args.through_version}"
        if args.include_minor:
            label += " (all releases)"
        else:
            label += " (major releases)"
        return f"{label}:"
    # date mode
    end_str = format_date_short(args.end_date) if args.end_date else "?"
    today_dt = datetime.strptime(args.today, "%Y-%m-%d")
    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else None
    year_suffix = ""
    if end_dt and end_dt.year != today_dt.year:
        year_suffix = f", {end_dt.year}"
    elif end_dt:
        year_suffix = f", {today_dt.year}"
    if args.include_minor:
        kind = "all"
    else:
        kind = "major"
    return f"RHOAI {kind} milestones, {today_str} – {end_str}{year_suffix}:"


def render_table(tasks, include_minor):
    lines = []
    if include_minor:
        lines.append("| # | Date | | Milestone |")
        lines.append("|---|------|-|-----------|")
    else:
        lines.append("| # | Date | Milestone |")
        lines.append("|---|------|-----------|")

    for i, t in enumerate(tasks, 1):
        date_col = format_date_range(t.get("date_start", t["date_finish"]), t["date_finish"])
        name_col = format_milestone_name(t["name"])
        if include_minor:
            star = "⭐" if not is_patch_milestone(t["name"]) else ""
            lines.append(f"| {i} | {date_col} | {star} | {name_col} |")
        else:
            lines.append(f"| {i} | {date_col} | {name_col} |")
    return "\n".join(lines)


def main():
    args = parse_args()
    data = read_input()

    # Handle both raw array and {data: [...]} wrapper
    if isinstance(data, dict):
        tasks = data.get("data", [])
    else:
        tasks = data

    # Filter out long-spanning grouping tasks
    tasks = [t for t in tasks if not is_date_range_task(t)]

    # Filter out browse_schedule level-0 tasks
    tasks = [t for t in tasks if t.get("level", 1) >= 1]

    # Deduplicate
    tasks = deduplicate(tasks)

    # Apply version/minor filters
    if args.through_version:
        tasks = filter_through_version(tasks, args.through_version, args.include_minor)
    elif not args.include_minor:
        tasks = [t for t in tasks if not is_patch_milestone(t["name"])]

    if not tasks:
        print("No milestones found matching the criteria.")
        return

    summary = build_summary(args, len(tasks))
    table = render_table(tasks, args.include_minor)
    print(f"{summary}\n\n{table}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        # --- Self-tests ---
        assert normalize_name("3.5 RHOAI GA") == "RHOAI GA"
        assert normalize_name("3.5 EA1 RHOAI RELEASE") == "RHOAI RELEASE"
        assert normalize_name("3.3.4 RHOAI Code Freeze") == "RHOAI Code Freeze"

        assert is_patch_milestone("3.3.4 RHOAI GA")
        assert is_patch_milestone("2.25.7 RHOAI GA")
        assert not is_patch_milestone("3.5 RHOAI GA")
        assert not is_patch_milestone("3.5 EA1 RHOAI RELEASE")

        assert is_z_entity("rhoai-3.5.z")
        assert not is_z_entity("rhoai-3.5")
        assert not is_z_entity("rhoai-3.5.EA1")

        t_good = {"draft": False, "flags": ["keydate", "roadmap"], "entity": {"shortname": "rhoai-3.5.z"}}
        t_bad = {"draft": True, "flags": ["keydate"], "entity": {"shortname": "rhoai-3.5.EA1"}}
        assert dedup_score(t_good) > dedup_score(t_bad)

        assert format_date_short("2026-06-17") == "Jun 17"
        assert format_date_short("2026-08-20") == "Aug 20"
        assert format_date_short("2026-12-01") == "Dec 1"

        assert "**" in format_date_range("2026-06-17", "2026-06-17")
        assert "–" in format_date_range("2026-07-14", "2026-07-15")

        assert "\U0001f9ca" in format_milestone_name("3.5 RHOAI Code Freeze")
        assert "**" in format_milestone_name("3.5 RHOAI GA")
        assert "\U0001f9ca" in format_milestone_name("3.5 RHOAI Feature Freeze")
        assert "**" not in format_milestone_name("3.5 Planning Freeze")

        assert extract_version("3.5 RHOAI GA") == "3.5"
        assert extract_version("3.3.4 RHOAI Code Freeze") == "3.3.4"
        assert extract_version("No version here") is None

        assert version_at_or_below("3.5", "3.6")
        assert version_at_or_below("3.6", "3.6")
        assert not version_at_or_below("3.7", "3.6")
        assert version_at_or_below("3.3.4", "3.5")
        assert version_at_or_below("2.25.7", "3.5")

        tasks = [
            {"name": "3.5 RHOAI GA", "date_finish": "2026-08-20", "date_start": "2026-08-20",
             "draft": False, "flags": ["ga", "keydate", "roadmap"], "entity": {"shortname": "rhoai-3.5.z"}},
            {"name": "3.5 RHOAI GA", "date_finish": "2026-08-20", "date_start": "2026-08-20",
             "draft": False, "flags": ["ga", "keydate", "roadmap"], "entity": {"shortname": "rhoai-3.5"}},
        ]
        deduped = deduplicate(tasks)
        assert len(deduped) == 1
        assert deduped[0]["entity"]["shortname"] == "rhoai-3.5.z"

        span_task = {"name": "3.6 Red Hat OpenShift AI", "date_start": "2026-09-23", "date_finish": "2026-11-20"}
        assert is_date_range_task(span_task)
        point_task = {"name": "3.5 RHOAI GA", "date_start": "2026-08-20", "date_finish": "2026-08-20"}
        assert not is_date_range_task(point_task)

        print("All format-milestones self-tests passed.")
        sys.exit(0)

    main()
