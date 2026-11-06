#!/bin/bash
# ============================================================
# UNETI AI - one-line install for macOS, no "cannot be opened" block
#
#   curl -fsSL https://raw.githubusercontent.com/uneti-ai/uneti-ai/main/packaging/macos/get-uneti.sh | bash
#
# Downloads the same UNETI-AI-macOS.dmg the website links to, copies UNETI AI.app into
# Applications, then runs its first-time install right here in this Terminal window.
# Why no Gatekeeper prompt: macOS only checks files a browser saved (they carry a quarantine
# flag), and the app is not signed with an Apple Developer ID yet. A file curl downloads
# carries no such flag.
# ============================================================
set -euo pipefail

URL="https://github.com/uneti-ai/uneti-ai/releases/download/desktop/UNETI-AI-macOS.dmg"
[ "$(uname -s)" = "Darwin" ] || { echo "This installer is for macOS. On Linux run ./install.sh from the repo."; exit 1; }

TMP="$(mktemp -d)"
MNT=""
cleanup() { [ -n "${MNT}" ] && hdiutil detach -quiet "${MNT}" 2>/dev/null; rm -rf "${TMP}"; }
trap cleanup EXIT

echo ""
echo "  UNETI AI: dang tai bo cai... (downloading)"
curl -fL --progress-bar -o "${TMP}/UNETI-AI-macOS.dmg" "${URL}"
MNT="$(hdiutil attach -nobrowse -readonly "${TMP}/UNETI-AI-macOS.dmg" | awk -F'\t' '/\/Volumes\//{print $NF}')"
[ -d "${MNT}/UNETI AI.app" ] || { echo "The disk image has no UNETI AI.app"; exit 1; }

# /Applications when it is writable (an admin account), else ~/Applications.
DEST="/Applications"
[ -w "${DEST}" ] || { DEST="${HOME}/Applications"; mkdir -p "${DEST}"; }
# Replace only the app bundle; the brain lives in ~/UNETI-AI and is never touched here.
rm -rf "${DEST}/UNETI AI.app"
cp -R "${MNT}/UNETI AI.app" "${DEST}/"
xattr -dr com.apple.quarantine "${DEST}/UNETI AI.app" 2>/dev/null || true
echo "  Da chep UNETI AI vao ${DEST} (copied to ${DEST})"

APP="${DEST}/UNETI AI.app"
if [ -d "${HOME}/UNETI-AI/.git" ] && [ -x "${HOME}/UNETI-AI/.venv/bin/python" ]; then
  echo "  UNETI AI da cai san, dang mo... (already installed, opening)"
  open "${APP}"
  exit 0
fi
# First install in THIS window. stdin is the curl pipe, so give the installer the keyboard
# back: install.sh asks for the UNETI AI admin account and may ask for the Mac password.
bash "${APP}/Contents/Resources/bootstrap.sh" < /dev/tty
