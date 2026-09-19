#!/usr/bin/env bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_DIR/deployment/oxygen.pid"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping Oxygen (PID: $PID)..."
        kill -TERM "$PID"
        # Wait up to 10 seconds for clean shutdown
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        rm -f "$PID_FILE"
        echo "Oxygen stopped."
        exit 0
    else
        echo "PID file exists but process $PID is not running. Removing stale PID file."
        rm -f "$PID_FILE"
    fi
fi

# Fallback: kill any orphaned gunicorn instances bound to 8016
PIDS=$(fuser 8016/tcp 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "Killing processes bound to port 8016: $PIDS"
    fuser -k -TERM 8016/tcp 2>/dev/null || true
    echo "Stopped."
else
    echo "No running Oxygen process found on port 8016."
fi
