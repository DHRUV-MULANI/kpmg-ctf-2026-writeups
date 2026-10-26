#!/usr/bin/env bash
T="https://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io/"
resp=$(curl -sk -m 20 -X POST --data-urlencode "page=$1" "$T")
if echo "$resp" | grep -q 'error-box'; then
  echo "[NOT FOUND] $1"
else
  echo "$resp" | sed -n '/<div class="viewer">/,/<\/div>/p' | sed 's/<div class="viewer">//; s/<\/div>//'
fi
