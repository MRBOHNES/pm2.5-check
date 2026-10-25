#!/usr/bin/env bash
# Fail if the built frontend does not contain the backend address.
# Catches a build where VITE_API_URL came out empty (e.g. stored as a Sensitive
# variable, which `vercel pull` cannot read), which the title-only smoke test misses.
set -euo pipefail

dir="${1:?usage: check_bundle.sh BUILD_DIR BACKEND_URL}"
url="${2:?usage: check_bundle.sh BUILD_DIR BACKEND_URL}"
url="${url%/}"

if grep -rqF --include='*.js' -- "$url" "$dir"; then
  echo "bundle ok: contains the backend address"
else
  echo "FAIL: no .js file in $dir contains the backend address. Is VITE_API_URL set as a plain (non-sensitive) variable for this environment?"
  exit 1
fi
