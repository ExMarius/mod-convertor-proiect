#!/usr/bin/env python3
"""Probare uke.progamer.me pas 2: SLP pe 15704 + SSH racco/1234 pe 22."""
import socket, struct, sys, json

HOST = "uke.progamer.me"

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

def slp(port):
    try:
        s = socket.create_connection((HOST, port), timeout=8); s.settimeout(8)
        p = varint(0) + varint(769) + varint(len(HOST)) + HOST.encode() + struct.pack(">H", port) + varint(1)
        s.sendall(varint(len(p)) + p); s.sendall(b"\x01\x00")
        read_varint(s); read_varint(s); ln = read_varint(s)
        raw = b""
        while len(raw) < ln:
            c = s.recv(ln - len(raw))
            if not c: break
            raw += c
        d = json.loads(raw.decode("utf-8", "ignore"))
        print(f"SLP :{port} OK: {d.get('version',{}).get('name','?')} protocol {d.get('version',{}).get('protocol','?')}")
        print(f"   motd: {str(d.get('description'))[:140]}")
        print(f"   players: {d.get('players',{}).get('online')}/{d.get('players',{}).get('max')}")
        s.close()
    except Exception as e:
        print(f"SLP :{port} EȘEC: {type(e).__name__}: {str(e)[:100]}")

# 1. serverul real pe 15704?
slp(15704)
# și încă câteva porturi comune în caz că
for p in []:
    slp(p)

# 2. SSH racco/1234 pe 22?
try:
    import paramiko
except ImportError:
    import os; os.system("pip3 install -q paramiko"); import paramiko

for user, pw in [("racco", "1234")]:
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(HOST, port=22, username=user, password=pw, timeout=15,
                  allow_agent=False, look_for_keys=False)
        print(f"SSH {user}@{HOST}: CONECTAT ✓✓✓")
        for cmd in ["whoami", "ls -la", "ls ~", "pwd"]:
            _, out, err = c.exec_command(cmd, timeout=15)
            o = out.read().decode("utf-8", "ignore")[:600]
            e = err.read().decode("utf-8", "ignore")[:200]
            print(f"$ {cmd}\n{o}{('  ERR:'+e) if e else ''}")
        c.close()
    except Exception as ex:
        print(f"SSH {user}: {type(ex).__name__}: {str(ex)[:200]}")
