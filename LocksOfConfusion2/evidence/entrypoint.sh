#!/bin/sh
set -e

# Root flag is written at container start from the FLAG env var, not
# baked in at build time, so one image can be run with any flag:
#   docker run -d -p 2222:22 -p 8813:8813 \
#     --cap-add=NET_ADMIN --cap-add=NET_RAW \
#     -e FLAG='CTF{...}' reactive-defense:ssh-target
# NOT `${FLAG:-CTF{...}}` -- shell parameter-expansion defaults don't
# respect inner braces, they terminate at the first `}` regardless of
# nesting, which leaks a stray trailing `}` into the result.
if [ -z "$FLAG" ]; then
    FLAG='CTF{root_flag_placeholder}'
fi

echo "$FLAG" > /root/root.txt
chmod 600 /root/root.txt
chmod 700 /root

exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf
