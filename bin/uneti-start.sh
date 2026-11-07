#!/bin/bash
# ============================================================
# UNETI AI - macOS launcher (start)
# Starts the FastAPI server (if not already running) and opens
# the dashboard in the default browser. No Docker required.
#
# Paths are resolved from this script's own location, so the repo
# can live anywhere. Run ./install.sh once first to create .venv.
# ============================================================
set -u

# Repo root = parent of this script's directory (bin/)
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# The port, in the server's own order: the environment, then .env, then 7777.
PORT="${UNETI_PORT:-$(sed -nE "s/^[[:space:]]*(export[[:space:]]+)?UNETI_PORT[[:space:]]*=[[:space:]]*[\"']?([0-9]+).*/\2/p" "${APP_DIR}/.env" 2>/dev/null | tail -1 || true)}"
PORT="${PORT:-7777}"
URL="http://127.0.0.1:${PORT}"
LOG="${APP_DIR}/server/uneti.log"
PIDF="${APP_DIR}/server/uneti.pid"
PY="${APP_DIR}/.venv/bin/python"

# A GUI (Finder/LaunchServices) launch starts with a minimal PATH, so add the
# common CLI locations - the server subprocess needs to find `claude` (the
# brain), plus node/ffmpeg/rg.
export PATH="${HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"
if command -v npm >/dev/null 2>&1; then
  NPM_BIN="$(npm prefix -g 2>/dev/null)/bin"
  [ -d "${NPM_BIN}" ] && export PATH="${NPM_BIN}:${PATH}"
fi

# Open the dashboard as an app window (no address bar, own Dock icon) when a Chromium browser
# is installed, the same way the Windows launcher uses Edge --app. Otherwise the default browser.
open_ui() {
  local b
  for b in "Google Chrome" "Microsoft Edge" "Brave Browser"; do
    if [ -d "/Applications/${b}.app" ] || [ -d "${HOME}/Applications/${b}.app" ]; then
      open -na "${b}" --args --app="${URL}" && return 0
    fi
  done
  open "${URL}"
}

# .env names another port than the login agent was given: rewrite the agent, which restarts the server on that port.
AGENT="${HOME}/Library/LaunchAgents/${UNETI_LAUNCHD_LABEL:-com.uneti.os}.plist"
if [ -f "${AGENT}" ] && ! grep -q "<string>${PORT}</string>" "${AGENT}"; then
  [ -f "${AGENT%.plist}.open.plist" ] || export UNETI_AUTOSTART_OPEN=0
  UNETI_PORT="${PORT}" bash "${APP_DIR}/bin/uneti-autostart.sh" install
  if [ "${UNETI_AUTOSTART_OPEN:-1}" = "0" ]; then
    for _ in $(seq 1 30); do
      sleep 1
      if curl -sf -o /dev/null "${URL}/" 2>/dev/null; then break; fi
    done
    open_ui
  fi
  exit 0
fi

# Already up? Just open it.
if curl -sf -o /dev/null "${URL}/" 2>/dev/null; then
  open_ui
  exit 0
fi

if [ ! -x "${PY}" ]; then
  osascript -e 'display alert "UNETI AI" message "Chua cai moi truong. Chay ./install.sh trong thu muc du an truoc."' 2>/dev/null || true
  echo "Missing venv at ${PY} - run ./install.sh first." >&2
  exit 1
fi

cd "${APP_DIR}/server" || exit 1
UNETI_STATE_DIR="${APP_DIR}/server" nohup "${PY}" \
  -m uvicorn main:app --host 127.0.0.1 --port "${PORT}" > "${LOG}" 2>&1 &
echo $! > "${PIDF}"

# Wait until healthy (max ~30s), then open the browser
for _ in $(seq 1 30); do
  sleep 1
  if curl -sf -o /dev/null "${URL}/" 2>/dev/null; then break; fi
done
open_ui
