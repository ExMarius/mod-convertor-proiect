#!/usr/bin/env python3
"""Rulează selftest-ul și prinde rezultatele individuale din consolă."""
import os, sys, json, time
import urllib.request, urllib.parse, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
LOG = open(f"{REP}/falix-selftest.txt", "a", encoding="utf-8")

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

log(f"=== {time.strftime('%H:%M:%S')} SELFTEST DETALIAT ===")
code, r = api("GET", "/servers?limit=100")
SID = next((s["id"] for s in (r.get("data", []) if code == 200 else [])
            if "offroader" in str(s.get("name", "")).lower()), None)
assert SID

# --- asigură-te că serverul e pornit ---
code, r = api("GET", f"/servers/{SID}/resources")
state = ((r.get("data") or {}).get("current_state") or "").lower()
log(f"stare server: {state or 'necunoscută'}")
if state not in ("running", "started"):
    code, r = api("POST", f"/servers/{SID}/power", body={"signal": "start"})
    if code in (200, 201, 202, 204):
        log("pornire trimisă, aștept „Done”...")
        for _ in range(36):
            time.sleep(10)
            t = get_log()
            if "Done (" in t:
                log("serverul e SUS ✓"); break
    else:
        err = (r.get("error") or {})
        log(f"power start → {code} ({err.get('code')})")
        if err.get("action_url"):
            log(f"LINK_VERIFICARE: {err['action_url']}")
        log("aștept până când utilizatorul completează verificarea (până la 50 min)...")
        for i in range(100):
            time.sleep(30)
            code, r = api("GET", f"/servers/{SID}/resources")
            state = ((r.get("data") or {}).get("current_state") or "").lower()
            if i % 4 == 0:
                log(f"  poll {i}: stare={state or '?'}")
            if state in ("running", "started"):
                log("serverul a pornit ✓ aștept „Done”...")
                for _ in range(30):
                    time.sleep(10)
                    t = get_log()
                    if "Done (" in t:
                        log("serverul e SUS ✓"); break
                break
        else:
            log("=== OPRIT: 50 min fără verificare ===")
            sys.exit(1)

send("execute as ExMarius at @s run function offroader:selftest")
time.sleep(22)
send("scoreboard players get #pass offr.tmp")
time.sleep(3)
send("scoreboard players get #fail offr.tmp")
time.sleep(6)

txt = get_log()
lines = txt.splitlines()
log("--- TOATE liniile TEST din log ---")
n = 0
for l in lines:
    if "TEST OK" in l or "TEST ESEC" in l or "TEST EȘEC" in l:
        log(f"  {l[:180]}"); n += 1
if n == 0:
    log(f"(nimic — log are {len(lines)} linii; ultima fereastră:)")
    for l in lines[-30:]:
        log(f"  | {l[:170]}")
log("=== GATA ===")
