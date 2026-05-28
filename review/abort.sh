#!/bin/bash
# Force-kill vibediff without flushing comments.
# Usage: abort.sh <PID> <PORT>
PID="$1"
PORT="$2"

if [ -z "$PID" ] || [ -z "$PORT" ]; then
  echo "Usage: abort.sh <vibediff_pid> <port>" >&2
  exit 1
fi

kill -9 "$PID" 2>/dev/null

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

echo "vibediff killed, comments discarded."
