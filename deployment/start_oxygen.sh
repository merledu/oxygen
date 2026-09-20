#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

PID_FILE="$PROJECT_DIR/deployment/oxygen.pid"
LOG_DIR="$PROJECT_DIR/deployment/logs"
mkdir -p "$LOG_DIR"
chown -R ar:ar "$LOG_DIR" 2>/dev/null || true
chmod -R 775 "$LOG_DIR" 2>/dev/null || true
chmod 664 "$LOG_DIR"/*.log 2>/dev/null || true

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Oxygen is already running with PID $(cat "$PID_FILE")."
    exit 0
fi

echo "Starting Oxygen Production Server on 0.0.0.0:8016..."
"$PROJECT_DIR/.venv/bin/gunicorn" oxygen.asgi:application \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8016 \
    --workers 1 \
    --backlog 2048 \
    --timeout 120 \
    --pid "$PID_FILE" \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log" \
    --daemon

sleep 1
if [ -f "$PID_FILE" ]; then
    echo "Oxygen started successfully. PID: $(cat "$PID_FILE")"
else
    echo "Oxygen started in background."
fi
