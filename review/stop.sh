#!/bin/bash
# Send SIGINT to vibediff so it flushes comments to stdout, then wait for exit.
# Usage: stop.sh <PID> <PORT> <output_file>
PID="$1"
PORT="$2"
OUTPUT_FILE="$3"

if [ -z "$PID" ] || [ -z "$PORT" ] || [ -z "$OUTPUT_FILE" ]; then
  echo "Usage: stop.sh <vibediff_pid> <port> <output_file>" >&2
  exit 1
fi

kill -INT "$PID" 2>/dev/null

# Close the vibediff browser surface in cmux if running inside cmux
if [ -n "$CMUX_WORKSPACE_ID" ] && command -v cmux &>/dev/null; then
  SURFACE_REF=$(cmux --json tree --workspace "$CMUX_WORKSPACE_ID" 2>/dev/null | python3 -c "
import json, sys
port = sys.argv[1]
tree = json.load(sys.stdin)
for w in tree.get('windows', []):
    for ws in w.get('workspaces', []):
        for p in ws.get('panes', []):
            for s in p.get('surfaces', []):
                if s.get('type') == 'browser' and ('localhost:' + port) in (s.get('url') or ''):
                    print(s['ref'])
                    sys.exit(0)
sys.exit(1)
" "$PORT" 2>/dev/null) && cmux close-surface --surface "$SURFACE_REF" &>/dev/null
fi

# Remove port lock file
rm -f "/tmp/vibediff-ports/$PORT"

sleep 2
cat "$OUTPUT_FILE"
