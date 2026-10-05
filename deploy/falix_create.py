#!/usr/bin/env python3
"""Creează (sau reutilizează) serverul Falix gratuit + deploy Offroader complet.

POST /servers (free, minecraft-java) → așteaptă instalarea → versiunea 1.21.4 →
upload plugin+datapack → resource-pack → power start → verificare consolă.
Idempotent: serverul numit „Offroader" e reutilizat dacă există.
"""
import os, sys, json, time, base64
import urllib.request, urllib.parse, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN, "FALIX_TOKEN lipsește"
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/falix-deploy.txt", "a", encoding="utf-8")

def log(m):
    print(m); LOG.write(m + "\n"); LOG.flush()

def api(method, path, body=None, raw=None, ctype="application/json", timeout=90):
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
                except Exception: return r.status, {"raw": txt[:500]}
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "ignore")
            try: rr = json.loads(txt)
            except Exception: rr = {"raw": txt[:500]}
            if e.code in (503, 429, 502) and attempt < 4:
                wait = 15 * (attempt + 1)
                log(f"  [{e.code}] retry în {wait}s ({path[:50]})")
                time.sleep(wait)
                continue
            return e.code, rr
        except Exception as e:
            if attempt < 4:
                time.sleep(10); continue
            return 0, {"error": {"code": "network", "message": str(e)}}
    return 0, {"error": {"code": "exhausted", "message": "prea multe reîncercări"}}

log("")
log(f"=== {time.strftime('%H:%M:%S')} CREARE + DEPLOY FALIX ===")

# ---------- 1. găsește sau creează ----------
code, r = api("GET", "/servers?limit=100")
servers = r.get("data", []) if code == 200 else []
SRV = next((s for s in servers if "offroader" in str(s.get("name", "")).lower()), None)

if SRV:
    SID = SRV["id"]
    log(f"server existent: {SRV.get('name')} (id={SID}, status={SRV.get('status')})")
else:
    log("creez server gratuit nou...")
    body = {
        "name": "Offroader-Test",
        "subdomain": "offroader-arena",
        "application": {"slug": "minecraft-java"},
        "plan": {"type": "free"},
        "eula_accepted": True,
        "visibility": "private",
    }
    code, r = api("POST", "/servers", body=body)
    log(f"POST /servers → {code}: {json.dumps(r, ensure_ascii=False)[:500]}")
    if code not in (200, 201, 202):
        # poate subdomeniul e luat
        body["subdomain"] = "offroader-exmarius1"
        code, r = api("POST", "/servers", body=body)
        log(f"retry POST /servers → {code}: {json.dumps(r, ensure_ascii=False)[:500]}")
    if code not in (200, 201, 202):
        sys.exit(1)
    d = r.get("data", {})
    SID = d.get("id") or d.get("server", {}).get("id")
    job = d.get("job_id") or d.get("job", {}).get("id")
    if not SID and job:
        log(f"job creare: {job} — poll...")
        for i in range(40):
            time.sleep(5)
            c2, r2 = api("GET", f"/account/servers/create-jobs/{job}")
            jd = r2.get("data", {})
            log(f"  job {i}: {json.dumps(jd, ensure_ascii=False)[:200]}")
            SID = jd.get("server_id") or (jd.get("server") or {}).get("id")
            if SID or jd.get("status") in ("failed", "error"):
                break
    if not SID:
        log("nu am primit id-ul serverului — opresc"); sys.exit(1)
    log(f"server creat: id={SID}")

# ---------- 2. așteaptă instalarea ----------
seen_full = False
for i in range(30):
    code, r = api("GET", f"/servers/{SID}")
    if code != 200:
        log(f"GET server → {code}: {json.dumps(r)[:200]}"); time.sleep(10); continue
    d = r.get("data", {}) or {}
    if not seen_full:
        log(f"obiect server complet: {json.dumps(d, ensure_ascii=False)[:700]}")
        seen_full = True
    st = d.get("status") or d.get("state") or d.get("current_state")
    if st:
        log(f"stare server: {st}")
        if "install" in str(st).lower():
            time.sleep(10); continue
    break
code, r = api("GET", f"/servers/{SID}")
full = r.get("data", {})
log(f"server: {json.dumps(full, ensure_ascii=False)[:600]}")

# ---------- 3. versiunea / aplicația (Paper 1.21.4 dacă se poate) ----------
code, r = api("GET", f"/servers/{SID}/startup")
if code == 200:
    log(f"startup: {json.dumps(r.get('data', {}), ensure_ascii=False)[:800]}")
else:
    log(f"GET startup → {code}")
code, r = api("GET", f"/servers/{SID}/settings/applications")
if code == 200:
    apps = r.get("data", [])
    log("aplicații comutabile (primele 10):")
    for a in (apps if isinstance(apps, list) else [apps])[:10]:
        log(f"  {json.dumps(a, ensure_ascii=False)[:240]}")
else:
    log(f"GET settings/applications → {code}")

# ---------- 4. structura fișierelor ----------
code, r = api("GET", f"/servers/{SID}/files?path=/")
root_files = []
if code == 200:
    fd = r.get("data", [])
    if isinstance(fd, dict): fd = fd.get("files", [])
    root_files = [f.get("name") for f in fd if isinstance(f, dict)]
log(f"root: {root_files[:25]}")
world = next((f for f in root_files if f and f.lower() in ("world", "worlds")), "world")
log(f"lumea: {world}")

# ---------- 5. upload ----------
def mkdirs(path):
    parts = path.strip("/").split("/")
    name = parts[-1]; parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
    code, r = api("POST", f"/servers/{SID}/files/folder", body={"name": name, "path": parent, "root": parent})
    log(f"mkdir {path} → {code}: {json.dumps(r)[:150]}")

def put_file(path, local):
    blob = open(local, "rb").read()
    log(f"upload {path} ({len(blob)} bytes)...")
    q = urllib.parse.quote(path)
    code, r = api("PUT", f"/servers/{SID}/files/content?path={q}", raw=blob,
                  ctype="application/octet-stream")
    if code in (200, 201, 204):
        log(f"  OK (raw)"); return True
    code, r = api("PUT", f"/servers/{SID}/files/content",
                  body={"path": path, "content": base64.b64encode(blob).decode()})
    if code in (200, 201, 204):
        log(f"  OK (base64)"); return True
    log(f"  eșuat: {code}: {json.dumps(r)[:250]}")
    return False

mkdirs("plugins")
mkdirs(f"{world}/datapacks")
ok1 = put_file("plugins/OffroaderPlugin.jar", "plugin/release/OffroaderPlugin.jar")
ok2 = put_file(f"{world}/datapacks/OffroaderDatapack.zip", "offroader/release/OffroaderDatapack.zip")

if not (ok1 and ok2):
    log("API write a eșuat → SFTP...")
    code, r = api("GET", f"/servers/{SID}/sftp")
    log(f"/sftp → {code}: {json.dumps(r, ensure_ascii=False)[:400]}")
    if code == 200:
        d = r.get("data", {})
        try:
            import paramiko
            c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(d.get("host"), port=int(d.get("port", 22)), username=d.get("username"),
                      password=d.get("password"), timeout=25, allow_agent=False, look_for_keys=False)
            sftp = c.open_sftp()
            for p, l in [("plugins/OffroaderPlugin.jar", "plugin/release/OffroaderPlugin.jar"),
                         (f"{world}/datapacks/OffroaderDatapack.zip", "offroader/release/OffroaderDatapack.zip")]:
                try:
                    sftp.put(l, p); log(f"  SFTP OK: {p} ({sftp.stat(p).st_size} b)")
                except IOError as e:
                    log(f"  SFTP {p}: {e}")
            ok1 = ok2 = True
            sftp.close(); c.close()
        except Exception as e:
            log(f"  SFTP eroare: {type(e).__name__}: {e}")

# ---------- 6. proprietăți ----------
RP = "https://github.com/ExMarius/mod-convertor-proiect/raw/arena%2F01a106d2-mod-convertor-proiect/offroader/release/OffroaderResourcePack.zip"
for body in ({"properties": {"resource-pack": RP}},
             {"resource-pack": RP}):
    code, r = api("PUT", f"/servers/{SID}/properties", body=body)
    log(f"properties → {code}: {json.dumps(r)[:200]}")
    if code in (200, 201, 204):
        break

# ---------- 7. pornire ----------
code, r = api("POST", f"/servers/{SID}/power", body={"signal": "start"})
log(f"power start → {code}: {json.dumps(r, ensure_ascii=False)[:400]}")
if code == 403:
    err = (r.get("error") or {})
    if err.get("code") == "verification_required":
        log("!! VERIFICARE NECESARĂ (o dată, în browser): deschide linkul ăsta:")
        log(f"!! {err.get('action_url')}")
        log("!! apoi îmi zici și repornesc deploy-ul (serverul e deja creat)")
        sys.exit(2)

# ---------- 8. așteaptă pluginul în consolă ----------
found = False
for i in range(40):
    time.sleep(6)
    code, r = api("GET", f"/servers/{SID}/console/log")
    if code == 200:
        d = r.get("data")
        text = d if isinstance(d, str) else json.dumps(d)
        if "OffroaderPlugin" in text or "offroader" in text.lower():
            found = True
            for l in text.splitlines():
                if "Offroader" in l or "Done (" in l:
                    log(f"  | {l[:170]}")
            break
        if i % 5 == 4:
            log(f"  încă aștept boot... (ultimul rând: {text.splitlines()[-1][:120] if text.splitlines() else '?'})")
log(f"plugin găsit în consolă: {'DA ✓' if found else 'NU — vezi raport'}")
log("=== FINAL ===")
