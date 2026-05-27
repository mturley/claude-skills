#!/bin/bash
# Force-kill vibediff without flushing comments.
# Usage: abort.sh <PID>
PID="$1"

if [ -z "$PID" ]; then
  echo "Usage: abort.sh <vibediff_pid>" >&2
  exit 1
fi

kill -9 "$PID" 2>/dev/null
echo "vibediff killed, comments discarded."
