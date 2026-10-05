#!/usr/bin/env python3
"""Probează api.falix.gg + client.falixnodes.net/api cu tokenul flx_live."""
import os, json
import urllib.request, urllib.error

TOKEN = os.environ.get("FALIX_TOKEN", "")

def req(url, method="GET", token=True, data=None, timeout=20):
    h = {"Accept": "application/json", "User-Agent": "Mozilla/5.0",
         "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {TOKEN}"
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read(500).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        try: b = e.read(300).decode("utf-8", "ignore")
        except Exception: b = ""
        return e.code, b
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"

TARGETS = [
    "https://api.falix.gg/",
    "https://api.falix.gg/docs",
    "https://api.falix.gg/openapi.json",
    "https://api.falix.gg/servers",
    "https://api.falix.gg/v1/servers",
    "https://api.falix.gg/me",
    "https://api.falix.gg/user",
    "https://api.falix.gg/v1/me",
    "https://api.falix.gg/account",
    "https://client.falixnodes.net/api/user",
    "https://client.falixnodes.net/api/servers",
    "https://client.falixnodes.net/api/me",
]

print(f"token: {TOKEN[:12]}...")
for t in TARGETS:
    code, body = req(t)
    print(f"{t:48} → {code}: {body[:220]}")

# POST power pe /servers (dacă /servers răspunde, încercăm și forma cu POST)
code, body = req("https://api.falix.gg/servers", method="POST", data={"action": "list"})
print(f"POST /servers → {code}: {body[:220]}")
