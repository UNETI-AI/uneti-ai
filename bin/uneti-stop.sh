#!/bin/bash
# ============================================================
# UNETI AI - macOS launcher (stop)
# ============================================================
set -u

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDF="${APP_DIR}/server/uneti.pid"
# The port, in the server's own order: the environment, then .env, then 7777.
PORT="${UNETI_PORT:-$(sed -nE "s/^[[:space:]]*(export[[:space:]]+)?UNETI_PORT[[:space:]]*=[[:space:]]*[\"']?([0-9]+).*/\2/p" "${APP_DIR}/.env" 2>/dev/null | tail -1 || true)}"
PORT="${PORT:-7777}"

HERE="$(cd "${APP_DIR}/server" && pwd -P)"
ours() { [ "$(lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')" = "${HERE}" ]; }

if [ -f "${PIDF}" ]; then
  pid="$(cat "${PIDF}")"
  if ours "${pid}"; then kill "${pid}" 2>/dev/null; fi
  rm -f "${PIDF}"
fi
for pid in $(lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN -t 2>/dev/null); do
  if ours "${pid}"; then
    kill "${pid}" 2>/dev/null
  else
    echo "Port ${PORT} belongs to another program (PID ${pid}). Left running."
  fi
done
echo "UNETI AI stopped."
