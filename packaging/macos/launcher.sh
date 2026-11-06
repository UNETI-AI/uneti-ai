#!/bin/bash
# ============================================================
# UNETI AI.app (the one inside UNETI-AI-macOS.dmg) - what a double-click runs.
#
# First run (no UNETI AI in ~/UNETI-AI yet): opens Terminal on bootstrap.sh, which checks the Mac,
# installs what is missing and starts UNETI AI. Terminal on purpose: the first install takes
# minutes and may ask for the Mac password once, so the person must SEE what happens.
# Every run after that: bin/uneti-start.sh, which only opens the window when UNETI AI is already
# up and starts it first when it is not. It never restarts a running server.
#
# Unlike the in-repo "UNETI AI.app" (which must stay inside the repo folder), this bundle can
# live in /Applications: it finds UNETI AI through UNETI_HOME, default ~/UNETI-AI.
# ============================================================
UNETI_HOME="${UNETI_HOME:-$HOME/UNETI-AI}"
RES="$(cd "$(dirname "$0")/../Resources" && pwd)"

if [ -d "${UNETI_HOME}/.git" ] && [ -x "${UNETI_HOME}/.venv/bin/python" ] && [ -x "${UNETI_HOME}/bin/uneti-start.sh" ]; then
  exec "${UNETI_HOME}/bin/uneti-start.sh"
fi

# macOS asks once whether "UNETI AI" may control Terminal. If the person clicks Don't Allow
# (or the prompt never shows), osascript fails and nothing would happen at all: fall back to
# putting the command on the clipboard, opening Terminal, and saying "paste it".
# Not `open -a Terminal bootstrap.sh`: a script copied off the downloaded .dmg carries the
# quarantine flag, and Gatekeeper blocks it when it is opened through LaunchServices.
if ! osascript - "${RES}/bootstrap.sh" "${UNETI_HOME}" <<'AS' >/dev/null 2>&1
on run argv
  tell application "Terminal"
    activate
    do script "UNETI_HOME=" & quoted form of (item 2 of argv) & " bash " & quoted form of (item 1 of argv)
  end tell
end run
AS
then
  # %q escapes spaces and quotes in a form both bash and zsh (the Terminal default) accept.
  printf 'UNETI_HOME=%q bash %q\n' "${UNETI_HOME}" "${RES}/bootstrap.sh" | pbcopy
  open -a Terminal
  osascript -e 'display alert "UNETI AI" message "Terminal is open. Paste (Cmd+V) and press Enter to install UNETI AI.\n\nTerminal da mo. Dan (Cmd+V) roi bam Enter de cai UNETI AI."' >/dev/null 2>&1 || true
fi
