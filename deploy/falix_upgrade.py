#!/usr/bin/env python3
"""Upgrade Falix: SFTP plugin+datapack → (start dacă e nevoie, cu așteptare
verificare) → reload confirm → selftest cu rezultate în consolă."""
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

def wait_done(minutes=7):
    for _ in range(minutes * 6):
        time.sleep(10)
        if "Done (" in get_log():
            return True
    return False

log(f"=== {time.strftime('%H:%M:%S')} UPGRADE v2.0 (mod 1:1 ca plugin) ===")
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

# --- SFTP: plugin + datapack (merge și cu serverul oprit) ---
code, r = api("GET", f"/servers/{SID}/sftp")
d = (r.get("data", {}) or {})
HOST, PORT, USER = d.get("hostname"), int(d.get("port") or 22), d.get("username")
import paramiko
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, key_filename=KEYPATH,
          timeout=30, allow_agent=False, look_for_keys=False)
sftp = c.open_sftp()
for remote, local in [("plugins/OffroaderPlugin.jar", "plugin/release/OffroaderPlugin.jar"),
                      ("world/datapacks/OffroaderDatapack.zip", "offroader/release/OffroaderDatapack.zip")]:
    sftp.put(local, remote)
    ok = sftp.stat(remote).st_size == os.path.getsize(local)
    log(f"  {remote}: {sftp.stat(remote).st_size}b {'OK' if ok else 'GRESIT!'}")
    if not ok: sys.exit(1)
sftp.close(); c.close()

# --- asigură serverul pornit (așteaptă verificarea până la 50 min) ---
state = ""
for _ in range(4):
    code, r = api("GET", f"/servers/{SID}/resources")
    state = ((r.get("data") or {}).get("current_state") or "").lower()
    if state in ("running", "started"):
        break
    # fallback: log-ul arată un server viu?
    t = get_log()
    if "Done (" in t and "Stopping" not in t.split("Done (")[-1]:
        state = "running"
        break
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
            if i % 4 == 0: log(f"  poll {i}: {st or '?'}")
            if st in ("running", "started"):
                started = True; break
        if not started:
            log("=== OPRIT: 50 min fără verificare (fișierele sunt totuși urcate) ===")
            sys.exit(1)
    log("aștept „Done”...")
    if not wait_done():
        log("AVERTISMENT: „Done” nu a apărut în 7 min — continui oricum")

# --- reload (reîncarcă pluginul ȘI datapack-ul, fără restart) ---
send("reload confirm")
time.sleep(15)

# --- selftest ---
send("execute as ExMarius at @s run function offroader:selftest")
time.sleep(25)
send("scoreboard players get #pass offr.tmp")
time.sleep(3)
send("scoreboard players get #fail offr.tmp")
time.sleep(6)

txt = get_log()
log("--- linii importante din consolă ---")
for l in txt.splitlines():
    ll = l[:185]
    if any(k in l for k in ("TEST OK", "TEST ESEC", "OffroaderPlugin", "#pass", "#fail",
                            "Reload complete", "Done (", "ERROR", "Exception")):
        log(f"  {ll}")
log("=== UPGRADE v2.0 FINALIZAT ===")
