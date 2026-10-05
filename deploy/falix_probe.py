#!/usr/bin/env python3
"""Descoperă API-ul Falix (api.falixnodes.net) cu token flx_live_..."""
import os, sys, json
import urllib.request, urllib.error

TOKEN = os.environ.get("FALIX_TOKEN", "").strip() or (sys.argv[1] if len(sys.argv) > 1 else "")
BASES = ["https://api.falixnodes.net"]
PATHS = [
    "/", "/docs", "/openapi.json", "/swagger.json", "/redoc",
    "/v1", "/v1/servers", "/v1/me", "/v1/user", "/v1/account",
    "/servers", "/me", "/user", "/account",
    "/api", "/api/servers", "/api/v1/servers", "/api/me",
]

def get(url, extra=None):
    h = {"Accept": "application/json", "User-Agent": "arena-agent/1.0",
         "Authorization": f"Bearer {TOKEN}"}
    if extra: h.update(extra)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read(400).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        try: body = e.read(200).decode("utf-8", "ignore")
        except Exception: body = ""
        return e.code, body
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"

print(f"token: {TOKEN[:12]}...({len(TOKEN)} chars)")
for base in BASES:
    code, body = get(base)
    print(f"\n=== {base} → {code}: {body[:160]}")
    for p in PATHS:
        if p == "/": continue
        code, body = get(base + p)
        if code not in (404, 405, 0):
            print(f"  {p:22} → {code}: {body[:200]}")
    # și cu X-API-Key
    code, body = get(base + "/servers", {"X-API-Key": TOKEN})
    print(f"  /servers (X-API-Key)   → {code}: {body[:200]}")
