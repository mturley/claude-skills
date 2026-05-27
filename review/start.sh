#!/bin/bash
# Launch vibediff in the foreground, capturing its PID for later SIGINT.
# Intended to be run with run_in_background: true from Claude Code.
vibediff --format json &
VIBEDIFF_PID=$!
echo "VIBEDIFF_PID=$VIBEDIFF_PID"
wait $VIBEDIFF_PID 2>/dev/null
