#!/usr/bin/env python3
"""Fetch unread Gmail metadata for email triage.

Runs 4 parallel searches, deduplicates, fetches metadata for all unique
messages, groups by thread, and writes a JSON file.

Uses only Python stdlib. Requires `gws` CLI to be authenticated.
"""

import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

SEARCHES = [
    {
        "name": "directly_addressed",
        "query": "is:unread to:me -from:noreply -from:no-reply -from:notifications@ category:personal",
        "max_results": 100,
    },
    {
        "name": "action_required",
        "query": "is:unread to:me subject:(action OR review OR approve OR sign OR deadline OR urgent OR ASAP OR reminder OR complete OR required OR overdue)",
        "max_results": 50,
    },
    {
        "name": "important_humans",
        "query": "is:unread is:important -from:jira -from:noreply -from:no-reply -from:notifications@ -from:notification@ -from:gemini-notes@ -from:hello@udemybusiness",
        "max_results": 100,
    },
    {
        "name": "mentions",
        "query": 'is:unread "mentioned you" OR "@Mike"',
        "max_results": 50,
    },
]

MAX_FETCH_WORKERS = 20


def run_gws(args, timeout=30):
    result = subprocess.run(
        ["gws"] + args,
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout, result.stderr, result.returncode


def search_messages(search):
    params = {
        "userId": "me",
        "q": search["query"],
        "maxResults": search["max_results"],
    }
    stdout, stderr, rc = run_gws([
        "gmail", "users", "messages", "list",
        "--params", json.dumps(params),
    ])
    if rc != 0:
        print(f"[warn] search '{search['name']}' failed: {stderr.strip()}", file=sys.stderr)
        return []
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        print(f"[warn] search '{search['name']}' returned invalid JSON", file=sys.stderr)
        return []
    return data.get("messages", [])


def parse_from(raw):
    """Parse 'Name <email>' into (name, email)."""
    match = re.match(r'^"?(.+?)"?\s*<(.+?)>$', raw.strip())
    if match:
        return match.group(1).strip().strip('"'), match.group(2).strip()
    if "@" in raw:
        return raw.strip(), raw.strip()
    return raw.strip(), ""


def fetch_message_metadata(msg_id):
    params = {
        "userId": "me",
        "id": msg_id,
        "format": "metadata",
        "metadataHeaders": ["Subject", "From", "Date", "To", "Cc"],
    }
    stdout, stderr, rc = run_gws([
        "gmail", "users", "messages", "get",
        "--params", json.dumps(params),
    ])
    if rc != 0:
        return None
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    headers = {}
    for h in data.get("payload", {}).get("headers", []):
        headers[h["name"]] = h["value"]

    from_name, from_email = parse_from(headers.get("From", ""))
    label_ids = data.get("labelIds", [])

    return {
        "id": msg_id,
        "threadId": data.get("threadId", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "from_name": from_name,
        "from_email": from_email,
        "date": headers.get("Date", ""),
        "to": headers.get("To", ""),
        "cc": headers.get("Cc", ""),
        "labels": label_ids,
        "internalDate": data.get("internalDate", "0"),
    }


def main():
    # Phase 1: Run all searches in parallel
    all_messages = []
    with ThreadPoolExecutor(max_workers=len(SEARCHES)) as pool:
        futures = {pool.submit(search_messages, s): s for s in SEARCHES}
        for future in as_completed(futures):
            search = futures[future]
            try:
                messages = future.result()
                print(f"[info] search '{search['name']}': {len(messages)} results", file=sys.stderr)
                all_messages.extend(messages)
            except Exception as e:
                print(f"[warn] search '{search['name']}' exception: {e}", file=sys.stderr)

    # Phase 2: Deduplicate by message ID
    seen_ids = set()
    unique_messages = []
    for msg in all_messages:
        mid = msg["id"]
        if mid not in seen_ids:
            seen_ids.add(mid)
            unique_messages.append(msg)

    total_scanned = len(all_messages)
    unique_count = len(unique_messages)
    print(f"[info] {total_scanned} total results, {unique_count} unique messages", file=sys.stderr)

    # Phase 3: Fetch metadata for all unique messages in parallel
    fetched = []
    failures = 0
    with ThreadPoolExecutor(max_workers=MAX_FETCH_WORKERS) as pool:
        futures = {pool.submit(fetch_message_metadata, msg["id"]): msg for msg in unique_messages}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    fetched.append(result)
                else:
                    failures += 1
            except Exception:
                failures += 1

    if failures:
        print(f"[warn] {failures} message fetches failed", file=sys.stderr)

    # Phase 4: Group by thread, sort messages within each thread by internalDate
    threads = {}
    for msg in fetched:
        tid = msg["threadId"]
        if tid not in threads:
            threads[tid] = {"messages": []}
        threads[tid]["messages"].append(msg)

    for tid, thread in threads.items():
        thread["messages"].sort(key=lambda m: int(m.get("internalDate", "0")))
        latest = thread["messages"][-1]
        thread["subject"] = latest["subject"]
        thread["message_count"] = len(thread["messages"])
        # Remove internalDate from individual messages (internal use only)
        for msg in thread["messages"]:
            msg.pop("internalDate", None)

    output = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_unread_scanned": total_scanned,
        "unique_messages": unique_count,
        "thread_count": len(threads),
        "threads": threads,
    }

    # Write to temp file
    tmp_dir = os.path.expanduser("~/tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(tmp_dir, f"email-triage-{timestamp}.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(out_path)


if __name__ == "__main__":
    main()
