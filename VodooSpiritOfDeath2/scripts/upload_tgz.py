#!/usr/bin/env python3
"""Upload a local file to the target via base64-over-stdin, then extract if it's a tgz.

Usage: upload_tgz.py <local_file> <remote_dir>
"""
import base64
import sys
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"


def main():
    local = sys.argv[1]
    rdir = sys.argv[2]
    name = local.split("/")[-1]

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS,
              timeout=30, allow_agent=False, look_for_keys=False)

    def run(cmd, timeout=90):
        _, out, err = c.exec_command(cmd, timeout=timeout)
        o = out.read().decode(errors="replace")
        e = err.read().decode(errors="replace")
        print("$ " + cmd)
        print(o.rstrip())
        if e.strip():
            print("[stderr]", e.strip())
        print("-" * 50)

    run("rm -rf %s; mkdir -p %s && echo ready" % (rdir, rdir))

    data = base64.b64encode(open(local, "rb").read())
    print("uploading %s (%d b64 bytes) -> %s/%s" % (local, len(data), rdir, name))
    chan = c.get_transport().open_session()
    chan.settimeout(120)
    chan.exec_command("base64 -d > %s/%s; echo RC=$?; ls -l %s/%s" % (rdir, name, rdir, name))
    time.sleep(0.4)
    for i in range(0, len(data), 32768):
        chan.sendall(data[i:i + 32768])
    chan.shutdown_write()
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

    run("cd %s && tar xzf %s && find . -maxdepth 2 -type f -exec ls -l {} \\;" % (rdir, name))
    c.close()


if __name__ == "__main__":
    main()
