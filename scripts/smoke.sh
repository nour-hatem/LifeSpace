#!/usr/bin/env bash
#
# Smoke checks for the running development servers. The API runs on API_PORT
# (default 8000) and the Vite dev server on WEB_PORT (default 5173).
set -u

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"

failures=0

pass() { printf 'PASS %s\n' "$1"; }
fail() {
  printf 'FAIL %s\n' "$1"
  failures=$((failures + 1))
}

check() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local body

  if body="$(curl -fsS --max-time 5 "$url")"; then
    if [ "$body" = "$expected" ]; then
      pass "$name: $url"
    else
      fail "$name: $url returned unexpected body: $body"
    fi
  else
    fail "$name: $url could not be reached"
  fi
}

check_contains() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local body

  if body="$(curl -fsS --max-time 5 "$url")"; then
    case "$body" in
      *"$expected"*) pass "$name: $url" ;;
      *) fail "$name: $url returned unexpected body: $body" ;;
    esac
  else
    fail "$name: $url could not be reached"
  fi
}

check "api health" "http://127.0.0.1:${API_PORT}/api/health" '{"status":"ok"}'
check "api ready" "http://127.0.0.1:${API_PORT}/api/health/ready" '{"status":"ready"}'
check "web proxy health" "http://127.0.0.1:${WEB_PORT}/api/health" '{"status":"ok"}'
check_contains "api tasks" "http://127.0.0.1:${API_PORT}/api/v1/tasks" 'items'

if [ "$failures" -gt 0 ]; then
  printf '\n%d smoke check(s) failed.\n' "$failures"
  exit 1
fi

printf '\nAll smoke checks passed.\n'
