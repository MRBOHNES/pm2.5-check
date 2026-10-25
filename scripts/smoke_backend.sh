#!/usr/bin/env bash
# Poll GET /health until it returns 200 (default: up to 120 s), then check that
# /peak?city=Delhi&days=30 returns valid JSON with a "peak" key.
set -euo pipefail

base="${1:?usage: smoke_backend.sh BASE_URL [max_seconds]}"
base="${base%/}"
max="${2:-120}"
deadline=$((SECONDS + max))

until [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$base/health")" = "200" ]; do
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "FAIL: $base/health did not return 200 within ${max}s"
    exit 1
  fi
  sleep 5
done
echo "health ok"

curl -fsS --max-time 90 "$base/peak?city=Delhi&days=30" | python3 -c '
import json, sys
d = json.load(sys.stdin)
assert "peak" in d and d["standard"] == 60, d
print("peak ok: source =", d["source"], "| peak =", d["peak"] and d["peak"]["date"])
'
