#!/usr/bin/env bash
#
# Local prerequisite checks for LifeSpace.
# Prints one line per check: "OK name: detail", "WARN name: detail", or
# "FAIL name: detail". Exits 1 when any check fails.
set -u

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

failures=0

ok() { printf 'OK %s: %s\n' "$1" "$2"; }
warn() { printf 'WARN %s: %s\n' "$1" "$2"; }
fail() {
  printf 'FAIL %s: %s\n' "$1" "$2"
  failures=$((failures + 1))
}

port_in_use() {
  ss -ltnH 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]$1\$"
}

# Node.js: ^22.22.2, ^24.15.0, or >=26.0.0.
node_ranges="^22.22.2 (22.22.2 up to below 23), ^24.15.0 (24.15.0 up to below 25), or 26.0.0 or newer"

version_ge() {
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n 1)" = "$2" ]
}

if command -v node >/dev/null 2>&1; then
  node_version="$(node --version 2>/dev/null | sed 's/^v//')"
  node_major="${node_version%%.*}"
  node_ok=0
  case "$node_major" in
    22) version_ge "$node_version" 22.22.2 && node_ok=1 ;;
    24) version_ge "$node_version" 24.15.0 && node_ok=1 ;;
    *)
      case "$node_major" in
        ''|*[!0-9]*) ;;
        *) [ "$node_major" -ge 26 ] && node_ok=1 ;;
      esac
      ;;
  esac
  if [ "$node_ok" = 1 ]; then
    ok node "v$node_version"
  else
    fail node "v$node_version is outside the accepted ranges: $node_ranges; switch with nvm use, or use the system Node"
  fi
else
  fail node "not found on PATH; accepted ranges: $node_ranges; switch with nvm use, or use the system Node"
fi

# npm.
if command -v npm >/dev/null 2>&1; then
  ok npm "v$(npm --version 2>/dev/null)"
else
  fail npm "not found on PATH"
fi

# uv.
if command -v uv >/dev/null 2>&1; then
  ok uv "v$(uv --version 2>/dev/null | awk '{print $2}')"
  # Python 3.14 reachable by uv without downloading an interpreter.
  if python_path="$(UV_PYTHON_DOWNLOADS=never uv python find 3.14 2>/dev/null)"; then
    ok python "$python_path"
  else
    fail python "uv cannot find Python 3.14 with UV_PYTHON_DOWNLOADS=never"
  fi
else
  fail uv "not found on PATH"
  fail python "cannot check because uv is missing"
fi

# Docker CLI and daemon.
if command -v docker >/dev/null 2>&1; then
  docker_context="$(docker context show 2>/dev/null || echo unknown)"
  if docker info >/dev/null 2>&1; then
    ok docker "daemon reachable, context $docker_context, server $(docker info --format '{{.ServerVersion}}' 2>/dev/null)"
  else
    fail docker "Docker daemon unreachable (active context: ${docker_context:-unknown}). On Docker Engine run: systemctl status docker (the service must be active and your user in the docker group) and docker context use default. On Docker Desktop start the app."
  fi
else
  fail docker "CLI not found on PATH (active context: unknown). On Docker Engine run: systemctl status docker (the service must be active and your user in the docker group) and docker context use default. On Docker Desktop start the app."
fi

# Free disk space on the filesystem that holds the repository.
disk_available_kb="$(df -Pk . 2>/dev/null | awk 'NR==2 {print $4}')"
disk_available_kb="${disk_available_kb:-0}"
disk_available_gb="$(awk -v kb="$disk_available_kb" 'BEGIN {printf "%.1f", kb / 1048576}')"
if [ "$disk_available_kb" -ge 3145728 ]; then
  ok disk "$disk_available_gb GB free (minimum 3 GB)"
else
  fail disk "$disk_available_gb GB free, below the 3 GB minimum"
fi

# Port 5433 belongs to the project database container only.
if port_in_use 5433; then
  owner_names="$(docker ps --filter publish=5433 --format '{{.Names}}' 2>/dev/null)"
  if printf '%s\n' "$owner_names" | grep -Eq '^lifespace'; then
    ok port5433 "listening, owned by the project database container ($(printf '%s' "$owner_names" | paste -sd, -))"
  else
    fail port5433 "listening but not owned by the project database container; free 127.0.0.1:5433 or run make db-up"
  fi
else
  ok port5433 "free (the database is not running; run make db-up)"
fi

# Ports used by the API and web dev servers.
for port in 8000 5173; do
  if port_in_use "$port"; then
    warn "port$port" "in use; stop the process before starting the dev server on 127.0.0.1:$port"
  else
    ok "port$port" "free"
  fi
done

# Port 5432 is the host PostgreSQL service, which this project never uses.
if port_in_use 5432; then
  warn port5432 "in use by the host PostgreSQL service; the project never uses it"
else
  ok port5432 "free (not used by this project either way)"
fi

# NODE_ENV is production in login shells; the web app neutralizes it.
if [ "${NODE_ENV:-}" = "production" ]; then
  warn NODE_ENV "is production; apps/web/.npmrc sets include=dev and the npm scripts run with env -u NODE_ENV, so devDependencies and the dev server are unaffected"
else
  ok NODE_ENV "${NODE_ENV:-unset}"
fi

if [ "$failures" -gt 0 ]; then
  printf '\n%d check(s) failed.\n' "$failures"
  exit 1
fi

printf '\nAll checks passed.\n'
