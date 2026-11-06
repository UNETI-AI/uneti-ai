#!/bin/bash
# Double-click in Finder to stop UNETI AI.
cd "$(dirname "$0")" || exit 1
bash "bin/uneti-stop.sh"
echo ""
echo "You can close this window."
