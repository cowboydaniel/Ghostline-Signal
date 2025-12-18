#!/usr/bin/env bash
#
# Start Ghostline Signal Rendezvous Server
# Simple wrapper script to start the server in the background
#

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PORT=${GHOSTLINE_RENDEZVOUS_PORT:-8080}
HOST=${GHOSTLINE_RENDEZVOUS_HOST:-0.0.0.0}

echo "Starting Ghostline Signal Rendezvous Server..."
echo "Host: $HOST"
echo "Port: $PORT"
echo ""

# Check if already running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "❌ Port $PORT is already in use!"
    echo "Either another server is running, or use a different port:"
    echo "  GHOSTLINE_RENDEZVOUS_PORT=9000 $0"
    exit 1
fi

# Start server
exec python3 rendezvous_server.py --host "$HOST" --port "$PORT"
