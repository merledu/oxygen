#!/usr/bin/env bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_DIR/deployment/oxygen.pid"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    if ps -p "$PID" >/dev/null 2>&1; then
        echo "Stopping Oxygen (PID: $PID)..."
        if ! kill -TERM "$PID" 2>/dev/null; then
            echo "Permission denied: process $PID is running under another user (e.g., root)."
            echo "Please run with sudo: sudo $0"
            exit 1
        fi
        # Wait up to 10 seconds for clean shutdown
        for i in {1..10}; do
            if ! ps -p "$PID" >/dev/null 2>&1; then
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

# Clean up any orphaned Spike processes
pkill -9 -f "tools/spike/bin/spike" 2>/dev/null || true
