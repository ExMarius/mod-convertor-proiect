#!/usr/bin/env python3
"""Citeste starea + consola serverului Falix si o salveaza in raport."""
import os, json, time
import urllib.request, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
OUT = open(f"{REP}/consola-live.txt", "w", encoding="utf-8")

def w(m):
    print(m); OUT.write(m + "\n"); OUT.flush()

def api(method, path, body=None, timeout=90):
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json",
         "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    for attempt in range(5):
        req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                txt = r.read().decode("utf-8", "ignore")
                try: return r.status, json.loads(txt)
                except Exception: return r.status, {"raw": txt}
        except urllib.error.HTTPError as e:
            try: rr = json.loads(e.read().decode("utf-8", "ignore"))
            except Exception: rr = {}
            if e.code in (503, 429, 502) and attempt < 4:
                time.sleep(12 * (attempt + 1)); continue
            return e.code, rr
        except Exception as e:
            if attempt < 4: time.sleep(8); continue
            return 0, {"error": str(e)}
    return 0, {"error": "exhausted"}

code, r = api("GET", "/servers?limit=100")
servers = r.get("data", []) if code == 200 else []
w(f"servere pe cont: {len(servers)}")
for s in servers:
    w(f"  - {s.get('name')} (id {s.get('id')})")
SID = next((s["id"] for s in servers if "offroader" in str(s.get("name", "")).lower()), None)
if not SID:
    w("niciun server offroader!"); raise SystemExit(1)

code, r = api("GET", f"/servers/{SID}/resources")
w(f"\nstare: {code} {json.dumps(r.get('data', {}))[:200]}")

code, r = api("GET", f"/servers/{SID}/console/log")
d = r.get("data") if code == 200 else None
lines = []
if isinstance(d, list): lines = [str(x) for x in d]
elif isinstance(d, dict):
    for k in ("lines", "log", "content", "text"):
        if k in d:
            v = d[k]
            lines = [str(x) for x in v] if isinstance(v, list) else str(v).splitlines()
            break
w(f"\n=== ULTIMELE 120 LINII DIN CONSOLĂ ({len(lines)} disponibile) ===")
for l in lines[-120:]:
    w(l[:200])
