#!/usr/bin/env python3
"""
Extract a summary of Claude Code sessions for a given date.

Scans all project directories under ~/.claude/projects/ for session files
modified on the target date, extracts user messages, and outputs a structured
summary grouped by project.

Usage:
    python3 extract-sessions.py [YYYY-MM-DD]

If no date is given, defaults to today.
Outputs markdown to stdout.
"""
import json
import os
import re
import sys
from datetime import datetime, date


def get_project_label(project_dir_name):
    """Convert a project directory name to a readable label.

    Claude Code encodes project paths by replacing '/' with '-' and prepending '-'.
    e.g. '-Users-mturley-git-rhoai-work' -> '~/git/rhoai-work'

    Since directory names can contain hyphens, we resolve ambiguity by checking
    which path actually exists on disk.
    """
    raw = project_dir_name.lstrip("-")
    parts = raw.split("-")

    # Try to reconstruct the real path by greedily joining segments
    # that form existing directories
    resolved = ["/"]
    i = 0
    while i < len(parts):
        # Try longest match first (greedy)
        found = False
        for end in range(len(parts), i, -1):
            candidate = "-".join(parts[i:end])
            test_path = os.path.join(*resolved, candidate)
            if os.path.exists(test_path):
                resolved.append(candidate)
                i = end
                found = True
                break
        if not found:
            # No match on disk — just use the segment as-is
            resolved.append(parts[i])
            i += 1

    path = os.path.join(*resolved)
    # Replace /Users/<username> with ~
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    return path


def extract_user_messages(filepath):
    """Extract user messages from a session JSONL file.

    Returns a list of dicts with 'timestamp' and 'text' keys.
    """
    messages = []
    try:
        with open(filepath, "r") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if obj.get("type") != "user":
                    continue

                timestamp = obj.get("timestamp", "")
                content = obj.get("message", {}).get("content", "")
                texts = []

                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "").strip()
                            # Skip system/XML content injected by IDE or hooks
                            if text and not text.startswith("<"):
                                # Strip skill preamble to get the actual user intent
                                # Skills start with "Base directory for this skill:"
                                if text.startswith("Base directory for this skill:"):
                                    # Try to find a section with arguments or user input
                                    # that reveals what the user actually invoked
                                    skill_match = re.search(
                                        r"^# (.+)$", text, re.MULTILINE
                                    )
                                    arg_match = re.search(
                                        r"## Arguments\s*\n\s*-\s*`([^`]+)`",
                                        text,
                                        re.MULTILINE,
                                    )
                                    if skill_match:
                                        skill_name = skill_match.group(1)
                                        if arg_match:
                                            texts.append(
                                                f"[Skill: {skill_name}] {arg_match.group(1)}"
                                            )
                                        else:
                                            texts.append(f"[Skill: {skill_name}]")
                                else:
                                    # Truncate long messages
                                    texts.append(text[:300])
                elif isinstance(content, str):
                    text = content.strip()
                    if text and not text.startswith("<"):
                        texts.append(text[:300])

                for text in texts:
                    messages.append({"timestamp": timestamp, "text": text})
    except (OSError, IOError):
        pass
    return messages


def find_sessions_for_date(target_date):
    """Find all session files modified on the target date.

    Returns a list of (project_label, filepath, messages) tuples,
    sorted by first message timestamp.
    """
    projects_dir = os.path.expanduser("~/.claude/projects")
    results = []

    if not os.path.isdir(projects_dir):
        return results

    for project_dir_name in os.listdir(projects_dir):
        project_path = os.path.join(projects_dir, project_dir_name)
        if not os.path.isdir(project_path):
            continue

        for filename in os.listdir(project_path):
            if not filename.endswith(".jsonl"):
                continue

            filepath = os.path.join(project_path, filename)

            # Check modification date
            try:
                mtime = os.path.getmtime(filepath)
                file_date = date.fromtimestamp(mtime)
                if file_date != target_date:
                    continue
            except OSError:
                continue

            # Skip subagent session files
            if "/subagents/" in filepath:
                continue

            messages = extract_user_messages(filepath)
            if not messages:
                # Session with no user messages (e.g. subagent-only) - skip
                continue

            label = get_project_label(project_dir_name)
            results.append((label, filepath, messages, mtime))

    # Sort by modification time
    results.sort(key=lambda x: x[3])
    return results


def format_time(timestamp_str):
    """Format an ISO timestamp to just HH:MM in local time."""
    if not timestamp_str:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        # Convert to local time
        dt = dt.astimezone()
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return ""


def main():
    if len(sys.argv) > 1:
        try:
            target_date = date.fromisoformat(sys.argv[1])
        except ValueError:
            print(f"Invalid date format: {sys.argv[1]}. Use YYYY-MM-DD.", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = date.today()

    sessions = find_sessions_for_date(target_date)

    if not sessions:
        print(f"No Claude sessions found for {target_date.isoformat()}.")
        sys.exit(0)

    # Group by project
    by_project = {}
    for label, filepath, messages, mtime in sessions:
        by_project.setdefault(label, []).append((filepath, messages, mtime))

    print(f"# Claude Activity for {target_date.isoformat()}")
    print(f"\n{len(sessions)} sessions across {len(by_project)} projects\n")

    for project_label, project_sessions in by_project.items():
        print(f"## {project_label}")
        print()
        for filepath, messages, mtime in project_sessions:
            session_id = os.path.basename(filepath).replace(".jsonl", "")[:8]
            # Filter messages to only those on the target date
            day_messages = []
            for msg in messages:
                msg_time = format_time(msg["timestamp"])
                if msg_time:
                    try:
                        dt = datetime.fromisoformat(
                            msg["timestamp"].replace("Z", "+00:00")
                        ).astimezone()
                        if dt.date() == target_date:
                            day_messages.append(msg)
                    except (ValueError, TypeError):
                        day_messages.append(msg)
                else:
                    day_messages.append(msg)

            if not day_messages:
                continue

            time_start = format_time(day_messages[0]["timestamp"])
            time_end = datetime.fromtimestamp(mtime).strftime("%H:%M")
            print(f"### Session {session_id} ({time_start}-{time_end})")
            print()
            for msg in day_messages:
                t = format_time(msg["timestamp"])
                prefix = f"[{t}] " if t else ""
                # Show first line only for multi-line messages
                first_line = msg["text"].split("\n")[0]
                if len(first_line) > 200:
                    first_line = first_line[:200] + "..."
                print(f"- {prefix}{first_line}")
            print()

    print(f"---")
    print(f"Total: {len(sessions)} sessions across {len(by_project)} projects")


if __name__ == "__main__":
    main()
