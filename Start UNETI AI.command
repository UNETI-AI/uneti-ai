#!/bin/bash
# Double-click in Finder to start UNETI AI and open the dashboard.
cd "$(dirname "$0")" || exit 1
bash "bin/uneti-start.sh"
echo ""
# The port, in the server's own order: the environment, then .env, then 7777.
PORT="${UNETI_PORT:-$(sed -nE "s/^[[:space:]]*(export[[:space:]]+)?UNETI_PORT[[:space:]]*=[[:space:]]*[\"']?([0-9]+).*/\2/p" ".env" 2>/dev/null | tail -1 || true)}"
PORT="${PORT:-7777}"
echo "UNETI AI is running at http://127.0.0.1:${PORT}"
echo "This window can be closed - the server keeps running in the background."
