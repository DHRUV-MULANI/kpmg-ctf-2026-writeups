#!/usr/bin/env python3
"""Run a command on the target with a PTY allocated (paramiko get_pty=True)."""
import sys
import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "id"
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS,
              timeout=30, allow_agent=False, look_for_keys=False)
    chan = c.get_transport().open_session()
    chan.get_pty()
    chan.settimeout(90)
    chan.exec_command(cmd)
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
    print("exit:", chan.recv_exit_status())
    c.close()


if __name__ == "__main__":
    main()