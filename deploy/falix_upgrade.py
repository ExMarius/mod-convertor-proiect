#!/usr/bin/env python3
"""Deploy VehicleMod (port 1:1) pe Falix: SFTP upload + curățare vechi + reload + test consolă."""
import os, sys, json, time
import urllib.request, urllib.parse, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/falix-upgrade.txt", "a", encoding="utf-8")

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
            try: rr = json.loads(e.read().decode("utf-8", "ignore"))
            except Exception: rr = {}
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

log(f"=== {time.strftime('%H:%M:%S')} DEPLOY VEHICLEMOD 1:1 (tot modul) ===")
code, r = api("GET", "/servers?limit=100")
SID = next((s["id"] for s in (r.get("data", []) if code == 200 else [])
            if "offroader" in str(s.get("name", "")).lower()), None)
assert SID
log(f"server id={SID}")

# --- cheia SSH ---
KEYPATH = "/tmp/falix_key"
blob = os.popen(f"openssl enc -d -aes-256-cbc -pbkdf2 -base64 -k '{os.environ['PTERO_TOKEN']}' -in deploy/falix_key.enc").read()
open(KEYPATH, "w").write(blob)
os.chmod(KEYPATH, 0o600)
PUB = os.popen(f"ssh-keygen -y -f {KEYPATH}").read().strip() + " arena-agent-falix"
code, r = api("GET", "/account/ssh-keys")
existing = r.get("data", []) if code == 200 else []
have = any(PUB.split()[1] in json.dumps(k) for k in existing)
if not have:
    for k in [k for k in existing if "arena-agent" in str(k.get("name", ""))]:
        api("DELETE", f"/account/ssh-keys/{k.get('id')}")
    code, r = api("POST", "/account/ssh-keys", body={"name": "arena-agent", "public_key": PUB})
    log(f"cheie SSH înregistrată: {code}")
    time.sleep(5)
else:
    log("cheia SSH e deja în cont")

# --- pornire dacă e nevoie (așteaptă verificarea până la 50 min) ---
state = ""
for _ in range(4):
    code, r = api("GET", f"/servers/{SID}/resources")
    state = ((r.get("data") or {}).get("current_state") or "").lower()
    if state in ("running", "started"):
        break
    t = get_log()
    if "Done (" in t and "Stopping" not in t.split("Done (")[-1]:
        state = "running"; break
    time.sleep(6)
log(f"stare server: {state or 'necunoscută'}")
if state not in ("running", "started"):
    code, r = api("POST", f"/servers/{SID}/power", body={"signal": "start"})
    if code not in (200, 201, 202, 204):
        err = (r.get("error") or {})
        log(f"power start → {code} ({err.get('code')})")
        if err.get("action_url"):
            log(f"LINK_VERIFICARE: {err['action_url']}")
        log("aștept verificarea utilizatorului (până la 50 min)...")
        started = False
        for i in range(100):
            time.sleep(30)
            code, r = api("GET", f"/servers/{SID}/resources")
            st = ((r.get("data") or {}).get("current_state") or "").lower()
            if st not in ("running", "started"):
                t = get_log()
                if "joined the game" in t or ("Done (" in t and "Stopping" not in t.split("Done (")[-1]):
                    st = "running"
            if i % 4 == 0: log(f"  poll {i}: {st or '?'}")
            if st in ("running", "started"):
                started = True; break
        if not started:
            log("=== OPRIT: 50 min fără verificare (fișierele sunt urcate) ===")
            sys.exit(1)
    log("aștept „Done”...")
    for _ in range(42):
        time.sleep(10)
        if "Done (" in get_log():
            log("serverul e SUS"); break

# --- SFTP ---
code, r = api("GET", f"/servers/{SID}/sftp")
d = (r.get("data", {}) or {})
HOST, PORT, USER = d.get("hostname"), int(d.get("port") or 22), d.get("username")
import paramiko
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
for attempt in range(3):
    try:
        c.connect(HOST, port=PORT, username=USER, key_filename=KEYPATH,
                  timeout=30, allow_agent=False, look_for_keys=False)
        break
    except Exception as e:
        log(f"  SFTP auth încercarea {attempt+1}: {e}")
        if attempt == 2: raise
        time.sleep(20)
sftp = c.open_sftp()

# curăță vechiul sistem (plugin offroader + datapack)
for old in ["plugins/OffroaderPlugin.jar", "world/datapacks/OffroaderDatapack.zip"]:
    try:
        sftp.remove(old); log(f"  șters vechi: {old}")
    except FileNotFoundError:
        pass
    except Exception as e:
        log(f"  {old}: {e}")

# urcă noul plugin
sftp.put("vehiclemod/release/VehicleMod.jar", "plugins/VehicleMod.jar")
ok = sftp.stat("plugins/VehicleMod.jar").st_size == os.path.getsize("vehiclemod/release/VehicleMod.jar")
log(f"  plugins/VehicleMod.jar: {sftp.stat('plugins/VehicleMod.jar').st_size}b {'OK' if ok else 'GRESIT!'}")
if not ok: sys.exit(1)
sftp.close(); c.close()

# --- curățenie: cai-zombie din testele vechi (lagau serverul 1457 ticks!) ---
send("kill @e[type=horse,tag=offr_veh]")
time.sleep(3)
send("kill @e[tag=offr_f]")
time.sleep(3)
send("kill @e[type=horse,tag=vm_veh]")
time.sleep(2)
send("kill @e[tag=vm_f]")
time.sleep(5)
log("curățenie zombie trimisă")

# --- reload (plugin + tot) și testul complet din consolă ---
send("reload confirm")
time.sleep(20)
send("vehicle test")
time.sleep(45)
send("version VehicleMod")
time.sleep(5)

txt = get_log()
log("--- linii importante din consolă ---")
for l in txt.splitlines():
    if any(k in l for k in ("VehicleMod", "TEST OK", "TEST ESEC", "FINAL:",
                            "Reload complete", "Done (", "ERROR", "Exception")):
        log(f"  {l[:185]}")
log("=== DEPLOY VEHICLEMOD FINALIZAT ===")
