#!/usr/bin/env python3
"""Probare uke.progamer.me: SLP pe 25565, RCON pe 25575 (parolă din argv/env), banner SSH.
Usage: python3 deploy/uke_probe.py [parolă_rcon]
"""
import socket, struct, sys, os

HOST = "uke.progamer.me"
RPORT = int(os.environ.get("UKE_RPORT", "25575"))
PW = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("UKE_PASS", "1234")

# ---------- 1. SLP pe 25565 ----------
def varint(n):
    out = b""
    while True:
        b = n & 0x7F; n >>= 7
        out += bytes([b | 0x80]) if n else bytes([b])
        if not n: return out

def read_varint(s):
    n = 0
    for i in range(5):
        d = s.recv(1)
        if not d: raise ConnectionError("inchis")
        n |= (d[0] & 0x7F) << (7*i)
        if not (d[0] & 0x80): return n

try:
    s = socket.create_connection((HOST, 25565), timeout=8); s.settimeout(8)
    p = varint(0) + varint(769) + varint(len(HOST)) + HOST.encode() + struct.pack(">H", 25565) + varint(1)
    s.sendall(varint(len(p)) + p); s.sendall(b"\x01\x00")
    read_varint(s); read_varint(s); ln = read_varint(s)
    raw = b""
    while len(raw) < ln:
        c = s.recv(ln - len(raw))
        if not c: break
        raw += c
    import json
    d = json.loads(raw.decode("utf-8", "ignore"))
    print(f"SLP 25565 OK: {d.get('version',{}).get('name','?')} — motd: {str(d.get('description'))[:100]}")
    print(f"            players: {d.get('players',{}).get('online')}/{d.get('players',{}).get('max')}")
    s.close()
except Exception as e:
    print(f"SLP 25565 EȘEC: {e}")

# ---------- 2. RCON pe 25575 ----------
def pkt(rid, ptype, payload):
    data = struct.pack("<ii", rid, ptype) + payload.encode() + b"\x00\x00"
    return struct.pack("<i", len(data)) + data

def read_pkt(s):
    raw = b""
    while len(raw) < 4:
        c = s.recv(4 - len(raw))
        if not c: raise ConnectionError("inchis")
        raw += c
    (ln,) = struct.unpack("<i", raw)
    body = b""
    while len(body) < ln:
        c = s.recv(ln - len(body))
        if not c: raise ConnectionError("inchis")
        body += c
    rid, ptype = struct.unpack("<ii", body[:8])
    return rid, ptype, body[8:-2].decode("utf-8", "ignore")

try:
    s = socket.create_connection((HOST, RPORT), timeout=10); s.settimeout(10)
    s.sendall(pkt(1, 3, PW))
    rid, _, _ = read_pkt(s)
    if rid == -1:
        print(f"RCON {RPORT}: parolă GREȘITĂ (server răspunde!)")
    else:
        print(f"RCON {RPORT}: AUTENTIFICAT ✓")
        for cmd in ["list", "version", "plugins" if False else "banlist players"]:
            s.sendall(pkt(2, 2, cmd))
            _, _, out = read_pkt(s)
            print(f"  > {cmd}\n    {out[:300] or '(gol)'}")
    s.close()
except Exception as e:
    print(f"RCON {RPORT} EȘEC: {type(e).__name__}: {e}")

# ---------- 3. SSH pe 25575 sau 22? ----------
for port in (25575, 22):
    try:
        s = socket.create_connection((HOST, port), timeout=6); s.settimeout(4)
        b = s.recv(48)
        print(f"SSH? :{port} banner={b[:40]!r}")
        s.close()
    except Exception as e:
        print(f":{port} → {type(e).__name__}: {str(e)[:80]}")
