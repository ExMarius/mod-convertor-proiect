#!/usr/bin/env python3
"""Falix pas 3: schema CreateServerRequest + applications + billing."""
import os, json
import urllib.request, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN, "FALIX_TOKEN lipsește din env"

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

print("=== /applications (auth) ===")
code, r = api("GET", "/applications")
print(code)
apps = r.get("data", []) if isinstance(r, dict) else []
for a in apps[:40]:
    if isinstance(a, dict):
        print(f"  {json.dumps(a, ensure_ascii=False)[:240]}")
if not apps:
    print(json.dumps(r, ensure_ascii=False)[:1200])

print("\n=== /account/billing/balance ===")
code, r = api("GET", "/account/billing/balance")
print(code, json.dumps(r, ensure_ascii=False)[:400])

print("\n=== CreateServerRequest din openapi ===")
req = urllib.request.Request(BASE + "/openapi.json")
with urllib.request.urlopen(req, timeout=60) as resp:
    spec = json.loads(resp.read().decode("utf-8", "ignore"))
schemas = spec.get("components", {}).get("schemas", {})
csr = schemas.get("CreateServerRequest", {})
print(json.dumps(csr, ensure_ascii=False, indent=1)[:4000])
# și $ref-urile din el
def refs(obj, seen=None):
    seen = seen or set()
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "$ref":
                out.append(v)
            else:
                out += refs(v, seen)
    elif isinstance(obj, list):
        for v in obj:
            out += refs(v, seen)
    return out
for ref in refs(csr):
    name = ref.split("/")[-1]
    s = schemas.get(name)
    if s:
        print(f"\n--- {name} ---")
        print(json.dumps(s, ensure_ascii=False, indent=1)[:1500])
