#!/usr/bin/env python3
"""Client RCON minimal (protocol Source RCON) pentru serverul local.
Usage: python3 deploy/rcon.py <comandă> [comandă...]
Adresă/parolă: env RCON_HOST (127.0.0.1), RCON_PORT (25575), RCON_PASS (arena-rcon).
"""
import os, socket, struct, sys

HOST = os.environ.get("RCON_HOST", "127.0.0.1")
PORT = int(os.environ.get("RCON_PORT", "25575"))
PW = os.environ.get("RCON_PASS", "arena-rcon")

def pkt(rid, ptype, payload):
    data = struct.pack("<ii", rid, ptype) + payload.encode("utf-8") + b"\x00\x00"
    return struct.pack("<i", len(data)) + data

def read_pkt(sock):
    raw = b""
    while len(raw) < 4:
        chunk = sock.recv(4 - len(raw))
        if not chunk:
            raise ConnectionError("conexiune închisă")
        raw += chunk
    (length,) = struct.unpack("<i", raw)
    body = b""
    while len(body) < length:
        chunk = sock.recv(length - len(body))
        if not chunk:
            raise ConnectionError("conexiune închisă")
        body += chunk
    rid, ptype = struct.unpack("<ii", body[:8])
    return rid, ptype, body[8:-2].decode("utf-8", "ignore")

s = socket.create_connection((HOST, PORT), timeout=10)
s.sendall(pkt(1, 3, PW))
rid, _, _ = read_pkt(s)
if rid == -1:
    print("AUTH EȘUAT (parolă greșită?)")
    sys.exit(1)

for cmd in sys.argv[1:]:
    s.sendall(pkt(2, 2, cmd))
    _, _, out = read_pkt(s)
    print(f"> {cmd}\n{out or '(fără răspuns)'}\n")
s.close()
