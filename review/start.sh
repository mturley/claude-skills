#!/bin/bash
# Launch vibediff on an allocated port, capturing its PID for later SIGINT.
# Intended to be run with run_in_background: true from Claude Code.

LOCK_DIR="/tmp/vibediff-ports"
mkdir -p "$LOCK_DIR"

# Clean up orphaned lock files (stale PIDs)
for lockfile in "$LOCK_DIR"/*; do
  [ -f "$lockfile" ] || continue
  old_pid=$(cat "$lockfile" 2>/dev/null)
  if [ -n "$old_pid" ] && ! kill -0 "$old_pid" 2>/dev/null; then
    rm -f "$lockfile"
  fi
done

# Find the first available port starting at 8889 (8888 is reserved for manual use)
PORT=8889
while [ -f "$LOCK_DIR/$PORT" ]; do
  PORT=$((PORT + 1))
done

cd "$(git rev-parse --show-toplevel)" || exit 1
vibediff --format json --port "$PORT" &
VIBEDIFF_PID=$!

# Write lock file with PID
echo "$VIBEDIFF_PID" > "$LOCK_DIR/$PORT"

echo "VIBEDIFF_PID=$VIBEDIFF_PID"
echo "VIBEDIFF_PORT=$PORT"
wait $VIBEDIFF_PID 2>/dev/null
