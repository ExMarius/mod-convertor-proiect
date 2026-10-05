#!/usr/bin/env python3
"""Fix v2: cheie SSH în contul Falix → SFTP binare → restart → selftest.
Fallback: datapack-ul ca folder de fișiere text (100% sigur prin API)."""
import os, sys, json, time, hashlib, subprocess
import urllib.request, urllib.parse, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/falix-fix2.txt", "a", encoding="utf-8")

def log(m):
    print(m); LOG.write(m + "\n"); LOG.flush()

def api(method, path, body=None, raw=None, ctype="application/json", timeout=120):
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    data = None
    if raw is not None:
        data = raw; h["Content-Type"] = ctype
    elif body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
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
    api("POST", f"/servers/{SID}/commands", body={"command": cmd})

log(f"=== {time.strftime('%H:%M:%S')} FIX v2: SSH KEY + SFTP ===")

code, r = api("GET", "/servers?limit=100")
SID = next((s["id"] for s in (r.get("data", []) if code == 200 else [])
            if "offroader" in str(s.get("name", "")).lower()), None)
assert SID, "server negăsit"
log(f"server id={SID}")

# ---------- 1. cheia mea SSH ----------
KEY = "/tmp/vps/arena_key"
if not os.path.exists(KEY):
    os.makedirs("/tmp/vps", exist_ok=True)
    subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-C", "arena-agent-falix",
                    "-f", KEY, "-q"], check=True)
PUB = open(KEY + ".pub").read().strip()
log(f"cheie publică: {PUB[:60]}...")

# listă chei existente
code, r = api("GET", "/account/ssh-keys")
existing = r.get("data", []) if code == 200 else []
log(f"chei existente în cont: {len(existing)}")
have = any(PUB.split()[1] in json.dumps(k) for k in existing)
if not have:
    code, r = api("POST", "/account/ssh-keys",
                  body={"name": "arena-agent", "public_key": PUB})
    log(f"POST ssh-key → {code}: {json.dumps(r, ensure_ascii=False)[:250]}")
    if code not in (200, 201, 202, 204):
        sys.exit(1)
else:
    log("cheia există deja în cont")

# ---------- 2. SFTP cu cheia ----------
code, r = api("GET", f"/servers/{SID}/sftp")
d = (r.get("data", {}) or {})
HOST = d.get("hostname"); PORT = int(d.get("port") or 22); USER = d.get("username")
log(f"SFTP: {USER}@{HOST}:{PORT}")

FILES = [("plugins/OffroaderPlugin.jar", "plugin/release/OffroaderPlugin.jar"),
         ("world/datapacks/OffroaderDatapack.zip", "offroader/release/OffroaderDatapack.zip")]

sftp_ok = {}
try:
    import paramiko
    for attempt in range(3):
        try:
            c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=PORT, username=USER, key_filename=KEY, timeout=30,
                      allow_agent=False, look_for_keys=False)
            break
        except Exception as e:
            log(f"  conectare SFTP (încercarea {attempt+1}): {type(e).__name__}: {str(e)[:150]}")
            time.sleep(12)
    else:
        raise RuntimeError("SFTP nu s-a conectat")
    log("  SFTP CONECTAT ✓")
    sftp = c.open_sftp()
    for remote, local in FILES:
        try:
            sftp.put(local, remote)
            st = sftp.stat(remote)
            ok = st.st_size == os.path.getsize(local)
            sftp_ok[remote] = ok
            log(f"  {remote}: {st.st_size}b → {'OK ✓' if ok else 'SIZE GREȘIT!'}")
        except Exception as e:
            log(f"  {remote}: {type(e).__name__}: {e}")
            sftp_ok[remote] = False
    sftp.close(); c.close()
except Exception as e:
    log(f"SFTP a eșuat: {type(e).__name__}: {e}")

# ---------- 3. fallback: datapack ca folder text ----------
if not sftp_ok.get("world/datapacks/OffroaderDatapack.zip"):
    log("datapack-ul zip nu s-a urcat → îl scriu ca folder (fișiere text)...")
    import pathlib
    src = pathlib.Path("offroader/datapack")
    n = 0
    for f in sorted(src.rglob("*")):
        if not f.is_file(): continue
        rel = f.relative_to(src).as_posix()
        remote = f"world/datapacks/offroader/{rel}"
        text = f.read_text(encoding="utf-8")
        code, r = api("PUT", f"/servers/{SID}/files/content",
                      body={"path": remote, "content": text})
        if code not in (200, 201, 204):
            log(f"  {remote} → {code}: {json.dumps(r)[:150]}")
        else:
            n += 1
    log(f"  scrise {n} fișiere text în world/datapacks/offroader/")
    if sftp_ok.get("world/datapacks/OffroaderDatapack.zip") is False:
        # șterge zip-ul corupt ca să nu mai dea warning
        api("POST", f"/servers/{SID}/files/delete", body={"files": ["world/datapacks/OffroaderDatapack.zip"]})

plugin_ok = sftp_ok.get("plugins/OffroaderPlugin.jar", False)
log(f"plugin jar: {'OK ✓' if plugin_ok else 'EȘUAT — necesită upload manual sau parolă SFTP'}")

# ---------- 4. restart ----------
code, r = api("POST", f"/servers/{SID}/power", body={"signal": "restart"})
log(f"power restart → {code}: {json.dumps(r, ensure_ascii=False)[:200]}")

# ---------- 5. verificări ----------
boot_ok = plug_ok = False
for i in range(50):
    time.sleep(6)
    txt = get_log()
    if "Done (" in txt: boot_ok = True
    if "OffroaderPlugin activ" in txt: plug_ok = True
    if boot_ok and plug_ok: break
log(f"boot={boot_ok} plugin={'DA ✓' if plug_ok else 'NU'}")

send("datapack list")
time.sleep(5)
txt = get_log()
for l in [l for l in txt.splitlines() if "file/" in l or "offroader" in l.lower()][-12:]:
    log(f"  | {l[:165]}")

# ---------- 6. selftest ----------
send("execute as ExMarius at @s run function offroader:selftest")
time.sleep(16)
send("scoreboard players get #pass offr.tmp")
time.sleep(3)
send("scoreboard players get #fail offr.tmp")
time.sleep(5)
txt = get_log()
log("--- rezultate ---")
for l in txt.splitlines()[-45:]:
    if any(k in l for k in ("#pass", "#fail", "Offroader", "offroader:", "Unknown", "Expected", "report")):
        log(f"  | {l[:175]}")
log("=== FIX v2 FINALIZAT ===")
