#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/stop_oxygen.sh"
sleep 1
"$DIR/start_oxygen.sh"
