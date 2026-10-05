#!/usr/bin/env python3
"""Doctor Falix: diagnostic + op + selftest, totul din consola prin API."""
import os, sys, json, time, re
import urllib.request, urllib.parse, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/falix-doctor.txt", "a", encoding="utf-8")

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
    if code != 200:
        return f"[log {code}: {json.dumps(r)[:150]}]"
    d = r.get("data")
    if isinstance(d, list):
        return "\n".join(str(x) for x in d)
    if isinstance(d, dict):
        for k in ("lines", "log", "content", "text"):
            if k in d:
                v = d[k]
                return "\n".join(str(x) for x in v) if isinstance(v, list) else str(v)
        return json.dumps(d)[:3000]
    return str(d)

def send(cmd):
    # schema auto-correct: încearcă "command", apoi câmpul din eroare
    for field in ("command", "commands", "cmd", "line", "input"):
        code, r = api("POST", f"/servers/{SID}/commands", body={field: cmd})
        if code in (200, 201, 202, 204):
            return True
        msg = json.dumps(r)
        m = re.search(r"missing field `([a-z_]+)`", msg)
        if m:
            continue
        log(f"command '{cmd[:40]}' → {code}: {msg[:200]}")
        return False
    return False

def wait_log(marker, timeout=30):
    t0 = time.time()
    seen = set()
    while time.time() - t0 < timeout:
        txt = get_log()
        for line in txt.splitlines():
            if marker in line and line not in seen:
                seen.add(line)
        if seen:
            return seen
        time.sleep(3)
    return seen

log("")
log(f"=== {time.strftime('%H:%M:%S')} DOCTOR FALIX ===")

# server id
code, r = api("GET", "/servers?limit=100")
SID = None
for s in (r.get("data", []) if code == 200 else []):
    if "offroader" in str(s.get("name", "")).lower():
        SID = s["id"]; log(f"server: {s.get('name')} id={SID}")
if not SID:
    log("serverul offroader nu apare!"); sys.exit(1)

# starea consolei
code, r = api("GET", f"/servers/{SID}/console/status")
log(f"console status → {code}: {json.dumps(r, ensure_ascii=False)[:300]}")

# log inițial (ultimele linii)
txt = get_log().splitlines()
log(f"--- ultimele 15 linii din consolă ---")
for l in txt[-15:]:
    log(f"  | {l[:165]}")

# 1. versiunea
send("version")
time.sleep(4)
txt = get_log()
m = re.findall(r"This server is running (v\S+ [^ ]+)", txt)
log(f"versiune server: {m[-1] if m else 'necunoscută'}")

# 2. cine e online
send("list")
time.sleep(4)
txt = get_log()
players = []
m = re.findall(r"players online: ?([\w, ]+)", txt)
if m:
    players = [p.strip() for p in m[-1].split(",") if p.strip()]
log(f"jucători online: {players}")

# 3. datapack-uri
send("datapack list")
time.sleep(4)
txt = get_log()
dp_lines = [l for l in txt.splitlines() if "datapack" in l.lower() or "file/" in l]
log("--- datapack list (ultimele) ---")
for l in dp_lines[-12:]:
    log(f"  | {l[:165]}")
enabled = any("offroader" in l.lower() for l in dp_lines)
if not enabled:
    log("datapack offroader NU apare — încerc activarea...")
    send('datapack enable "file/OffroaderDatapack.zip"')
    time.sleep(5)
    send("datapack list")
    time.sleep(4)
    txt = get_log()
    dp_lines = [l for l in txt.splitlines() if "file/" in l or "datapack" in l.lower()]
    for l in dp_lines[-8:]:
        log(f"  | {l[:165]}")

# 4. plugin?
txt = get_log()
plug = [l for l in txt.splitlines() if "OffroaderPlugin" in l]
log(f"linii OffroaderPlugin în log: {len(plug)}")
for l in plug[-5:]:
    log(f"  | {l[:165]}")

# 5. op jucătorii online
for p in players:
    send(f"op {p}")
    log(f"op {p} trimis")
time.sleep(3)

# 6. selftest ca jucător (dacă e cineva online + datapack activ)
if players and enabled:
    p = players[0]
    log(f"rulez selftest ca {p}...")
    send(f"execute as {p} at @s run function offroader:selftest")
    time.sleep(15)
    send("scoreboard players get #pass offr.tmp")
    time.sleep(3)
    send("scoreboard players get #fail offr.tmp")
    time.sleep(4)
    txt = get_log()
    res = [l for l in txt.splitlines() if "#pass" in l or "#fail" in l or "Offroader" in l]
    log("--- rezultate ---")
    for l in res[-15:]:
        log(f"  | {l[:165]}")
elif not players:
    log("nimeni online — sar selftest-ul")
elif not enabled:
    log("datapack inactiv — selftest inutil până se activează")

# log final
txt = get_log().splitlines()
log("--- finalul consolei ---")
for l in txt[-12:]:
    log(f"  | {l[:165]}")
log("=== DOCTOR FINALIZAT ===")
