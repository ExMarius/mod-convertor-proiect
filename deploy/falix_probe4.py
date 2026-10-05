#!/usr/bin/env python3
"""Falix pas 2: serverele raw, applications, init templates, schema POST /servers."""
import os, json
import urllib.request, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")

def api(method, path, body=None, timeout=60):
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json",
         "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", "ignore")
            try: return r.status, json.loads(txt)
            except Exception: return r.status, {"raw": txt[:600]}
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "ignore")
        try: return e.code, json.loads(txt)
        except Exception: return e.code, {"raw": txt[:600]}
    except Exception as e:
        return 0, {"error": str(e)}

print("=== /servers RAW ===")
code, r = api("GET", "/servers?limit=100")
print(code, json.dumps(r, ensure_ascii=False)[:800])

print("\n=== /applications ===")
code, r = api("GET", "/applications")
print(code, json.dumps(r, ensure_ascii=False)[:1500])

print("\n=== /init/templates ===")
code, r = api("GET", "/init/templates")
print(code, json.dumps(r, ensure_ascii=False)[:800])

print("\n=== openapi.json: căi + schema POST /servers ===")
req = urllib.request.Request(BASE + "/openapi.json",
                             headers={"Authorization": f"Bearer {TOKEN}"})
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        spec = json.loads(resp.read().decode("utf-8", "ignore"))
    print(f"{len(spec.get('paths', {}))} căi în spec")
    for p in sorted(spec.get("paths", {})):
        methods = ",".join(m.upper() for m in spec["paths"][p] if m in ("get", "post", "put", "patch", "delete"))
        print(f"  {methods:14} {p}")
    ps = spec.get("paths", {}).get("/servers", {}).get("post", {})
    print("\n--- POST /servers schema ---")
    print(json.dumps(ps.get("requestBody", {}), ensure_ascii=False)[:3000])
except Exception as e:
    print(f"openapi: {type(e).__name__}: {e}")
