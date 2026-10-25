#!/usr/bin/env bash
# Fetch the page: it must answer 200 and its HTML must contain "PM2.5 Check".
set -euo pipefail

url="${1:?usage: smoke_frontend.sh URL}"
html="$(curl -fsS --max-time 30 --retry 3 --retry-delay 5 "$url")"
if ! grep -q "PM2.5 Check" <<<"$html"; then
  echo "FAIL: $url answered but the HTML has no 'PM2.5 Check'"
  exit 1
fi
echo "frontend ok: $url"
