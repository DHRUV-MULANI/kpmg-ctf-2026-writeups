#!/usr/bin/env python3
"""
Interactive shell over SSH using paramiko invoke_shell() -- this allocates a REAL
pty (like `ssh -t`), which is what sudo's requiretty-style policy needs.
Sends commands one at a time and prints output.
"""
import sys
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"


def main():
    cmds = sys.argv[1:] if len(sys.argv) > 1 else ["id"]
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS,
              timeout=30, allow_agent=False, look_for_keys=False)
    chan = c.invoke_shell()
    chan.settimeout(5)
    time.sleep(1.0)
    try:
        chan.recv(65536)  # drain banner/prompt
    except Exception:
        pass

    for cmd in cmds:
        print("$ " + cmd)
        chan.send(cmd + "\n")
        time.sleep(1.2)
        buf = b""
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                d = chan.recv(65536)
                if not d:
                    break
                buf += d
            except Exception:
                break
        sys.stdout.write(buf.decode(errors="replace"))
        print()
    c.close()


if __name__ == "__main__":
    main()