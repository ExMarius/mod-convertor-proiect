#!/usr/bin/env python3
"""Curăță entitățile-zombie de pe server (cai offroader pierduți + piese) prin consolă."""
import os, json, time
import urllib.request, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
LOG = open(f"{REP}/falix-clean.txt", "a", encoding="utf-8")

def log(m):
    print(m); LOG.write(m + "\n"); LOG.flush()

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
SID = next((s["id"] for s in (r.get("data", []) if code == 200 else [])
            if "offroader" in str(s.get("name", "")).lower()), None)
assert SID

def send(cmd):
    log(f"  > {cmd}")
    return api("POST", f"/servers/{SID}/commands", body={"command": cmd})

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

code, r = api("GET", f"/servers/{SID}/resources")
state = ((r.get("data") or {}).get("current_state") or "").lower()
log(f"=== {time.strftime('%H:%M:%S')} CURĂȚENIE (stare: {state or '?'}) ===")

if state not in ("running", "started"):
    t = get_log()
    if "joined the game" in t or ("Done (" in t and "Stopping" not in t.split("Done (")[-1]):
        state = "running"
    else:
        log("serverul nu rulează — nimic de curățat acum.")
        raise SystemExit(0)

# numără entitățile problematice
send("execute if entity @e[type=horse,tag=offr_veh] run say CAI_OFFROADER: există")
time.sleep(4)
# omoară tot ce ține de vechiul sistem
send("kill @e[type=horse,tag=offr_veh]")
time.sleep(2)
send("kill @e[tag=offr_f]")
time.sleep(2)
send("kill @e[type=horse,tag=vm_veh]")
time.sleep(2)
send("kill @e[tag=vm_f]")
time.sleep(6)
send("say CURATENIE FINALIZATA")
time.sleep(4)

txt = get_log()
for l in txt.splitlines()[-25:]:
    log(f"  | {l[:180]}")
