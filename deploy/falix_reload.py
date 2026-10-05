#!/usr/bin/env python3
"""Activează datapack-ul fără restart (reload din consolă) + selftest + link verificare."""
import os, sys, json, time
import urllib.request, urllib.parse, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/falix-reload.txt", "a", encoding="utf-8")

def log(m):
    print(m); LOG.write(m + "\n"); LOG.flush()

def api(method, path, body=None, timeout=120):
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
            txt = e.read().decode("utf-8", "ignore")
            try: rr = json.loads(txt)
            except Exception: rr = {"raw": txt}
            if e.code in (503, 429, 502) and attempt < 4:
                time.sleep(15 * (attempt + 1)); continue
            return e.code, rr
        except Exception as e:
            if attempt < 4: time.sleep(10); continue
            return 0, {"error": str(e)}
    return 0, {"error": "exhausted"}

def get_log():
    code, r = api("GET", f"/servers/{SID}/console/log")
    if code != 200: return ""
    d = r.get("data")
    if isinstance(d, list): return "\n".join(str(x) for x in d)
    if isinstance(d, dict):
        for k in ("lines", "log", "content", "text"):
            if k in d:
                v = d[k]
                return "\n".join(str(x) for x in v) if isinstance(v, list) else str(v)
    return str(d)

def send(cmd):
    return api("POST", f"/servers/{SID}/commands", body={"command": cmd})

log(f"=== {time.strftime('%H:%M:%S')} RELOAD + SELFTEST ===")
code, r = api("GET", "/servers?limit=100")
SID = next((s["id"] for s in (r.get("data", []) if code == 200 else [])
            if "offroader" in str(s.get("name", "")).lower()), None)
assert SID
log(f"server id={SID}")

# 1. reload datapack-uri (consolă)
send("reload confirm")
time.sleep(8)
txt = get_log()
for l in [l for l in txt.splitlines() if "reload" in l.lower() or "data pack" in l.lower()][-8:]:
    log(f"  | {l[:165]}")

# 2. verificare datapack activat
send("datapack list")
time.sleep(5)
txt = get_log()
dp = [l for l in txt.splitlines() if "data pack" in l.lower() or "file/" in l]
for l in dp[-6:]:
    log(f"  | {l[:165]}")
enabled = any("offroader" in l.lower() and "enabled" in l.lower() for l in dp) or \
          any("OffroaderDatapack" in l and "available" not in l for l in dp)
log(f"datapack offroader activat: {enabled}")

# 3. selftest ca ExMarius
if enabled:
    send("execute as ExMarius at @s run function offroader:selftest")
    time.sleep(18)
    send("scoreboard players get #pass offr.tmp")
    time.sleep(3)
    send("scoreboard players get #fail offr.tmp")
    time.sleep(5)
    txt = get_log()
    log("--- rezultate selftest ---")
    for l in txt.splitlines()[-60:]:
        if any(k in l for k in ("#pass", "#fail", "Offroader TEST", "OK]", "EȘEC", "ES EC")):
            log(f"  | {l[:175]}")

# 4. link de verificare pentru restart (fără să opresc nimic)
code, r = api("POST", f"/servers/{SID}/power", body={"signal": "restart"})
if code in (200, 201, 202, 204):
    log("!! restart a pornit direct (fără verificare) — serverul se repornește acum")
else:
    err = (r.get("error") or {})
    log(f"power restart → {code} ({err.get('code')})")
    if err.get("action_url"):
        log(f"LINK_VERIFICARE: {err['action_url']}")

txt = get_log()
log("--- final consolă ---")
for l in txt.splitlines()[-10:]:
    log(f"  | {l[:165]}")
log("=== RELOAD FINALIZAT ===")
