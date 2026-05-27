#!/bin/bash
# Send SIGINT to vibediff so it flushes comments to stdout, then wait for exit.
# Usage: stop.sh <PID> <output_file>
PID="$1"
OUTPUT_FILE="$2"

if [ -z "$PID" ] || [ -z "$OUTPUT_FILE" ]; then
  echo "Usage: stop.sh <vibediff_pid> <output_file>" >&2
  exit 1
fi

kill -INT "$PID" 2>/dev/null
sleep 2
cat "$OUTPUT_FILE"
