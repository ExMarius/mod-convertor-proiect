#!/usr/bin/env python3
"""Server List Ping (protocol Minecraft) — verifică dacă serverul din sandbox
e reachable din internet, pe căile candidate.
Usage: python3 deploy/slp.py host:port [host:port ...]
"""
import socket, struct, json, sys

def varint(n):
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            out += bytes([b])
            return out

def read_varint(sock):
    n = 0
    for i in range(5):
        d = sock.recv(1)
        if not d:
            raise ConnectionError("conexiune închisă")
        b = d[0]
        n |= (b & 0x7F) << (7 * i)
        if not (b & 0x80):
            return n

def slp(host, port, timeout=8):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
    except Exception as e:
        return {"ok": False, "error": f"connect: {e}"}
    try:
        s.settimeout(timeout)
        payload = varint(0x00) + varint(769) + varint(len(host)) + host.encode() + struct.pack(">H", port) + varint(1)
        s.sendall(varint(len(payload)) + payload)
        s.sendall(b"\x01\x00")
        read_varint(s)            # lungime totală
        pid = read_varint(s)      # packet id (0x00)
        if pid != 0:
            return {"ok": False, "error": f"packet id neașteptat: {pid}"}
        ln = read_varint(s)       # lungime JSON
        raw = b""
        while len(raw) < ln:
            c = s.recv(ln - len(raw))
            if not c:
                break
            raw += c
        return {"ok": True, "resp": json.loads(raw.decode("utf-8", "ignore"))}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        s.close()

if __name__ == "__main__":
    for target in sys.argv[1:]:
        host, port = target.rsplit(":", 1)
        r = slp(host, int(port))
        if r["ok"]:
            d = r["resp"]
            ver = d.get("version", {}).get("name", "?")
            desc = str(d.get("description", ""))[:120]
            players = d.get("players", {})
            print(f"OK   {target} → {ver}, jucători {players.get('online')}/{players.get('max')}, motd: {desc}")
        else:
            print(f"EȘEC {target} → {r['error']}")
