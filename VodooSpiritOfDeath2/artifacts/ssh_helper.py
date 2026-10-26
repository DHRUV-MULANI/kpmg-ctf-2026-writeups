#!/usr/bin/env python3
"""
Helper for "Vodoo Spirit of Death - 2" (KPMG CTF).
* run()      -> one-shot command over SSH (paramiko)
* put_file() -> upload a local file to the target through an SSH exec channel
                (base64 over stdin). Needed because /tmp and /dev/shm may not be
                writable by the low-priv user; /run/lock often is.
"""
import base64
import sys
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"   # leaked in Redis DM message:thread:dm-baron-maya


def connect():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS,
              timeout=30, allow_agent=False, look_for_keys=False)
    return c


def run(c, command, timeout=40):
    _, out, err = c.exec_command(command, timeout=timeout)
    o = out.read().decode(errors="replace")
    e = err.read().decode(errors="replace")
    print("$ " + command)
    print(o)
    if e.strip():
        print("[stderr]", e)
    print("-" * 60)
    return o


def put_file(c, local_path, remote_path):
    data = base64.b64encode(open(local_path, "rb").read())
    chan = c.get_transport().open_session()
    chan.exec_command("base64 -d > %s; echo RC=$?" % remote_path)
    time.sleep(0.3)
    for i in range(0, len(data), 16384):
        chan.sendall(data[i:i + 16384])
    chan.shutdown_write()
    chan.settimeout(60)
    buf = b""
    try:
        while True:
            d = chan.recv(65536)
            if not d:
                break
            buf += d
    except Exception:
        pass
    print(buf.decode(errors="replace"))


if __name__ == "__main__":
    c = connect()
    run(c, "id; hostname; uname -a")
    c.close()
