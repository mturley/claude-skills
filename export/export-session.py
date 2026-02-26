#!/usr/bin/env python3
"""
Export a Claude Code session to readable markdown.

Usage:
    python3 export-session.py <session-file.jsonl> [output-file.md]

If output file is not specified, prints to stdout.
"""
import json
import sys
import re
from datetime import datetime


def extract_text_content(content, msg_type='assistant'):
    """Extract readable text from message content"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    # Clean up IDE tags and system reminders
                    text = re.sub(r'<ide_opened_file>.*?</ide_opened_file>\s*', '', text)
                    text = re.sub(r'<ide_selection>.*?</ide_selection>\s*', '', text, flags=re.DOTALL)
                    text = re.sub(r'<system-reminder>.*?</system-reminder>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<command-message>.*?</command-message>\s*', '', text)
                    text = re.sub(r'<command-name>.*?</command-name>', '', text)
                    if text.strip():
                        parts.append(text)
                elif item.get('type') == 'tool_result':
                    # This is a user response to a tool (e.g., AskUserQuestion answer, plan rejection)
                    tool_content = item.get('content', '')
                    if isinstance(tool_content, str):
                        # Check if it's a question answer
                        if 'User has answered your questions:' in tool_content:
                            # Extract the Q&A pairs
                            parts.append(f"\n**User answered questions:**\n{tool_content}\n")
                        # Check if it's a plan mode rejection with feedback
                        elif "user doesn't want to proceed" in tool_content and "reason for the rejection:" in tool_content:
                            # Extract just the user's reason
                            match = re.search(r'reason for the rejection:\s*(.+)$', tool_content, re.DOTALL)
                            if match:
                                reason = match.group(1).strip()
                                parts.append(f"\n**User feedback:** {reason}\n")
                        # Check if it's an approved plan
                        elif "User has approved your plan" in tool_content and "## Approved Plan:" in tool_content:
                            # Extract the approved plan content
                            match = re.search(r'## Approved Plan:\n(.+)$', tool_content, re.DOTALL)
                            if match:
                                plan_content = match.group(1).strip()
                                # Use 4 backticks to allow nested code blocks with 3 backticks
                                parts.append(f"\n**Plan approved by user:**\n\n<details>\n<summary>Approved plan</summary>\n\n````markdown\n{plan_content}\n````\n\n</details>\n")
                        # Skip other tool results (bash output, file reads, etc.) for cleaner export
                elif item.get('type') == 'tool_use':
                    tool_name = item.get('name', 'unknown')
                    tool_input = item.get('input', {})
                    if tool_name == 'Bash':
                        cmd = tool_input.get('command', '')
                        desc = tool_input.get('description', '')
                        if desc:
                            parts.append(f"\n**Tool: Bash** - {desc}\n```bash\n{cmd}\n```\n")
                        else:
                            parts.append(f"\n**Tool: Bash**\n```bash\n{cmd}\n```\n")
                    elif tool_name == 'Read':
                        path = tool_input.get('file_path', '')
                        parts.append(f"\n**Tool: Read** `{path}`\n")
                    elif tool_name == 'Write':
                        path = tool_input.get('file_path', '')
                        content = tool_input.get('content', '')
                        # Include full content for plan files
                        if '/plans/' in path and content:
                            # Use 4 backticks to allow nested code blocks with 3 backticks
                            parts.append(f"\n**Tool: Write** `{path}`\n\n<details>\n<summary>Plan content</summary>\n\n````markdown\n{content}\n````\n\n</details>\n")
                        else:
                            parts.append(f"\n**Tool: Write** `{path}`\n")
                    elif tool_name == 'Edit':
                        path = tool_input.get('file_path', '')
                        parts.append(f"\n**Tool: Edit** `{path}`\n")
                    elif tool_name == 'Glob':
                        pattern = tool_input.get('pattern', '')
                        parts.append(f"\n**Tool: Glob** `{pattern}`\n")
                    elif tool_name == 'Grep':
                        pattern = tool_input.get('pattern', '')
                        parts.append(f"\n**Tool: Grep** `{pattern}`\n")
                    elif tool_name == 'Task':
                        desc = tool_input.get('description', '')
                        parts.append(f"\n**Tool: Task** ({desc})\n")
                    elif tool_name == 'TodoWrite':
                        parts.append(f"\n**Tool: TodoWrite**\n")
                    elif tool_name == 'AskUserQuestion':
                        questions = tool_input.get('questions', [])
                        q_texts = [q.get('question', '') for q in questions]
                        parts.append(f"\n**Tool: AskUserQuestion**\n" + "\n".join(f"- {q}" for q in q_texts) + "\n")
                    elif tool_name == 'ExitPlanMode':
                        parts.append(f"\n**Tool: ExitPlanMode**\n")
                    elif tool_name == 'WebFetch':
                        url = tool_input.get('url', '')
                        parts.append(f"\n**Tool: WebFetch** `{url}`\n")
                    elif tool_name == 'Skill':
                        skill = tool_input.get('skill', '')
                        parts.append(f"\n**Tool: Skill** `/{skill}`\n")
                    else:
                        parts.append(f"\n**Tool: {tool_name}**\n")
        return ''.join(parts)
    return str(content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export-session.py <session-file.jsonl> [output-file.md]", file=sys.stderr)
        sys.exit(1)

    session_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    messages = []
    seen_content = set()  # Track content hashes to deduplicate session replays

    with open(session_file, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get('type') in ['user', 'assistant']:
                    msg_type = entry['type']
                    timestamp = entry.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass

                    content = entry.get('message', {}).get('content', [])
                    text = extract_text_content(content, msg_type)

                    # Include all messages with content, deduplicating by content hash
                    if text.strip():
                        # Create hash of message type + first 500 chars of content for dedup
                        content_key = f"{msg_type}:{text[:500]}"
                        if content_key in seen_content:
                            continue
                        seen_content.add(content_key)

                        messages.append({
                            'type': msg_type,
                            'timestamp': timestamp,
                            'text': text
                        })
            except json.JSONDecodeError:
                continue

    # Build markdown output
    output = []
    output.append("# Claude Code Session Export\n")
    output.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.append("---\n")

    for msg in messages:
        role = "**User**" if msg['type'] == 'user' else "**Assistant**"
        output.append(f"\n## {role}\n")
        if msg['timestamp']:
            output.append(f"*{msg['timestamp']}*\n")
        output.append(f"\n{msg['text']}\n")
        output.append("\n---\n")

    result = '\n'.join(output)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(result)
        print(f"Exported {len(messages)} messages to {output_file}")
    else:
        print(result)


if __name__ == '__main__':
    main()
