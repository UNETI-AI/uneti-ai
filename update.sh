#!/usr/bin/env bash
# ============================================================================
# UNETI AI - cập nhật lên bản mới nhất từ GitHub.
#   ./update.sh            (tự nhận Docker hay native)
#   ./update.sh docker     (ép chế độ Docker)
#   ./update.sh native     (ép chế độ native/systemd)
# ============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
MODE="${1:-auto}"
SUDO=""; [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1 && SUDO="sudo"

# Tên bản UNETI AI Ở THƯ MỤC NÀY. Nhiều bản trên cùng VPS thì mỗi bản một .env riêng; không đọc
# .env ở đây thì `./update.sh` của bản này đi restart container/dịch vụ của bản khác.
if [ -z "${UNETI_NAME:-}" ] && [ -f .env ]; then
  UNETI_NAME="$(sed -n 's/^[[:space:]]*UNETI_NAME[[:space:]]*=[[:space:]]*//p' .env | tail -1)"
fi
NAME="${UNETI_NAME:-uneti}"

echo "==> Pulling the latest code from GitHub..."
git pull --ff-only

is_docker() {
  command -v docker >/dev/null 2>&1 && [ -f docker-compose.yml ] && \
  docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$NAME"
}

if [ "$MODE" = "docker" ] || { [ "$MODE" = "auto" ] && is_docker; }; then
  echo "==> Docker → pulling the new image from GHCR and restarting..."
  # Đang bật HTTPS (Caddy)? Giữ nguyên override để cập nhật KHÔNG gỡ mất Caddy.
  HTTPS_ARGS=""
  if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qx "$NAME-caddy"; then
    HTTPS_ARGS="-f docker-compose.yml -f docker-compose.https.yml"
    echo "==> Caddy (HTTPS) detected → keeping the HTTPS setup."
  fi
  # Đứng sau proxy dùng chung (nhiều bản, mỗi bản một tên miền) thì giữ luôn override multi,
  # không thì lượt cập nhật này gỡ mất nhãn Caddy và bản đó rơi khỏi proxy.
  if [ -f docker-compose.multi.yml ] && docker network inspect uneti-web >/dev/null 2>&1; then
    HTTPS_ARGS="-f docker-compose.yml -f docker-compose.multi.yml"
    echo "==> Shared proxy (uneti-web) detected → keeping the multi-instance setup."
  fi
  # Đã mở cổng 8000 cho đăng nhập Google Workspace (docker-compose.google.yml, issue #855)? Giữ lại.
  if [ -f docker-compose.google.yml ] && docker port "$NAME" 8000 >/dev/null 2>&1; then
    HTTPS_ARGS="${HTTPS_ARGS:--f docker-compose.yml} -f docker-compose.google.yml"
    echo "==> Google sign-in port (8000) detected → keeping it."
  fi
  docker compose $HTTPS_ARGS pull
  docker compose $HTTPS_ARGS up -d
  echo "==> Done. Follow the logs:  docker compose logs -f"
else
  echo "==> Native → updating Python libraries and restarting the service..."
  [ -d .venv ] && ./.venv/bin/pip install -r requirements.txt -q || true
  # Updating Python alone leaves the ChatGPT model catalog on an old Codex CLI.
  if command -v npm >/dev/null 2>&1; then
    if ! npm install -g @openai/codex@latest && ! $SUDO npm install -g @openai/codex@latest; then
      echo "[!] Could not update Codex; the ChatGPT model list may be out of date."
    fi
  else
    echo "[!] npm not found; update Codex by hand to get the newest ChatGPT models."
  fi
  if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q "^$NAME\.service"; then
    $SUDO systemctl restart "$NAME"
    echo "==> Restarted. Follow the logs:  journalctl -u $NAME -f"
  elif [ "$(uname)" = "Darwin" ] && \
       launchctl print "gui/$(id -u)/${UNETI_LAUNCHD_LABEL:-com.uneti.os}" >/dev/null 2>&1; then
    # Mac chạy dưới launchd (KeepAlive): kill PID rồi tự chạy nohup là đua bind cổng với bản
    # launchd respawn ([Errno 48], vụ 14/08/2026). Để launchd tự đổi ca bằng kickstart -k.
    TARGET="gui/$(id -u)/${UNETI_LAUNCHD_LABEL:-com.uneti.os}"
    echo "==> launchd ($TARGET) detected → kickstart -k..."
    launchctl kickstart -k "$TARGET"
    echo "==> Asked launchd to restart UNETI AI. Logs: server/uneti.log"
  else
    # Mac / Linux không systemd: kill tiến trình đang giữ cổng rồi chạy lại nền (như install.sh)
    # The port, in the server's own order: the environment, then .env, then 7777.
    PORT="${UNETI_PORT:-$(sed -nE "s/^[[:space:]]*(export[[:space:]]+)?UNETI_PORT[[:space:]]*=[[:space:]]*[\"']?([0-9]+).*/\2/p" ".env" 2>/dev/null | tail -1 || true)}"
    PORT="${PORT:-7777}"
    # Only this copy's server: the port can belong to another program, and every browser with the page open has it too.
    PIDS=""
    for p in $(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null || true); do
      if [ "$(lsof -a -p "$p" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')" = "$(cd server && pwd -P)" ]; then
        PIDS="$PIDS $p"
      fi
    done
    if [ -n "$PIDS" ]; then
      echo "==> Stopping the old process (PID: $PIDS)..."
      kill $PIDS 2>/dev/null || true
      sleep 2
    fi
    ( cd server && UNETI_STATE_DIR="$PWD" nohup ../.venv/bin/python -m uvicorn main:app \
        --host "${UNETI_HOST:-127.0.0.1}" --port "$PORT" > uneti.log 2>&1 & )
    echo "==> Restarted (nohup). Logs: server/uneti.log"
  fi
fi
