#!/usr/bin/env python3
"""Repară fișierele binare corupte pe Falix + restart + selftest."""
import os, sys, json, time, base64, hashlib, re
import urllib.request, urllib.parse, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
assert TOKEN
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/falix-fix.txt", "a", encoding="utf-8")

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

log(f"=== {time.strftime('%H:%M:%S')} FIX BINARE + RESTART ===")

code, r = api("GET", "/servers?limit=100")
SID = next((s["id"] for s in (r.get("data", []) if code == 200 else [])
            if "offroader" in str(s.get("name", "")).lower()), None)
assert SID, "server negăsit"
log(f"server id={SID}")

# --- 0. schema write din openapi ---
try:
    req = urllib.request.Request(BASE + "/openapi.json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        spec = json.loads(resp.read().decode("utf-8", "ignore"))
    op = spec["paths"][f"/servers/{{server_id}}/files/content"]["put"]
    sch = json.dumps(op.get("requestBody", {}), ensure_ascii=False)
    log(f"schema PUT content: {sch[:1200]}")
except Exception as e:
    log(f"openapi: {e}")

FILES = [("plugins/OffroaderPlugin.jar", "plugin/release/OffroaderPlugin.jar"),
         ("world/datapacks/OffroaderDatapack.zip", "offroader/release/OffroaderDatapack.zip")]

def verify(remote, blob):
    """citește fișierul înapoi și compară md5"""
    q = urllib.parse.quote(remote)
    code, r = api("GET", f"/servers/{SID}/files/content?path={q}")
    if code != 200:
        log(f"  verify GET → {code}: {json.dumps(r)[:150]}"); return False
    d = r.get("data")
    got = None
    if isinstance(d, dict):
        c = d.get("content") or d.get("text") or d.get("data") or ""
        got = c.encode("utf-8", "ignore") if isinstance(c, str) else c
    elif isinstance(d, str):
        got = d.encode("utf-8", "ignore")
    if got is None:
        return False
    ok = hashlib.md5(got).hexdigest() == hashlib.md5(blob).hexdigest()
    log(f"  verify: remote {len(got)}b vs local {len(blob)}b → {'IDENTICE ✓' if ok else 'DIFERITE'}")
    return ok

results = {}
for remote, local in FILES:
    blob = open(local, "rb").read()
    b64 = base64.b64encode(blob).decode()
    log(f"[{remote}] {len(blob)} bytes, md5={hashlib.md5(blob).hexdigest()[:10]}")
    ok = False
    # varianta 1: encoding base64 declarat
    code, r = api("PUT", f"/servers/{SID}/files/content",
                  body={"path": remote, "content": b64, "encoding": "base64"})
    log(f"  PUT b64+encoding → {code}: {json.dumps(r)[:180]}")
    if code in (200, 201, 204):
        ok = verify(remote, blob)
    # varianta 2: câmp dedicat
    if not ok:
        code, r = api("PUT", f"/servers/{SID}/files/content",
                      body={"path": remote, "content_base64": b64})
        log(f"  PUT content_base64 → {code}: {json.dumps(r)[:180]}")
        if code in (200, 201, 204):
            ok = verify(remote, blob)
    # varianta 3: base64 în content, fără encoding (ceea ce a corupt înainte) — acum verificăm
    if not ok:
        code, r = api("PUT", f"/servers/{SID}/files/content",
                      body={"path": remote, "content": b64})
        log(f"  PUT b64 simplu → {code}")
        if code in (200, 201, 204):
            ok = verify(remote, blob)
    # varianta 4: raw cu ?path=
    if not ok:
        q = urllib.parse.quote(remote)
        code, r = api("PUT", f"/servers/{SID}/files/content?path={q}", raw=blob,
                      ctype="application/octet-stream")
        log(f"  PUT raw+query → {code}: {json.dumps(r)[:180]}")
        if code in (200, 201, 204):
            ok = verify(remote, blob)
    results[remote] = ok

# --- SFTP pentru ce a rămas nefiind OK ---
if not all(results.values()):
    log("API write insuficient → SFTP")
    code, r = api("GET", f"/servers/{SID}/sftp")
    if code == 200:
        d = r.get("data", {}) or {}
        host = d.get("host") or d.get("hostname") or d.get("ip")
        port = int(d.get("port") or 22)
        user = d.get("username") or d.get("user")
        pw = d.get("password") or d.get("secret")
        log(f"SFTP: {user}@{host}:{port} (parolă: {'prezentă' if pw else 'LIPSEȘTE — vezi raport'})")
        if host and user and pw:
            try:
                import paramiko
                c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                c.connect(host, port=port, username=user, password=pw, timeout=30,
                          allow_agent=False, look_for_keys=False)
                sftp = c.open_sftp()
                for remote, local in FILES:
                    if results.get(remote): continue
                    sftp.put(local, remote)
                    st = sftp.stat(remote)
                    ok = st.st_size == os.path.getsize(local)
                    log(f"  SFTP {remote}: {st.st_size}b → {'OK ✓' if ok else 'SIZE GREȘIT'}")
                    results[remote] = ok
                sftp.close(); c.close()
            except Exception as e:
                log(f"  SFTP eroare: {type(e).__name__}: {e}")
        else:
            log(f"  câmpuri SFTP disponibile: {list(d.keys())}")
            log(f"  date complete (fără parolă): {json.dumps({k:v for k,v in d.items() if 'pass' not in k.lower()}, ensure_ascii=False)[:400]}")
    else:
        log(f"GET /sftp → {code}: {json.dumps(r)[:300]}")

log(f"rezultate: {results}")
if not all(results.values()):
    log("nu toate fișierele s-au urcat corect — opresc pentru analiză")
    sys.exit(1)

# --- restart ---
code, r = api("POST", f"/servers/{SID}/power", body={"signal": "restart"})
log(f"power restart → {code}: {json.dumps(r, ensure_ascii=False)[:250]}")

# --- așteaptă boot + plugin ---
boot_ok = plug_ok = dp_ok = False
for i in range(50):
    time.sleep(6)
    txt = get_log()
    if "Done (" in txt and not boot_ok:
        boot_ok = True
        log("boot complet")
    if "OffroaderPlugin activ" in txt:
        plug_ok = True
    if "file/OffroaderDatapack.zip" in txt and "Missing metadata" not in txt.split("file/OffroaderDatapack.zip")[-1][:200]:
        dp_ok = True
    if boot_ok and plug_ok:
        break
log(f"boot={boot_ok} plugin={'DA ✓' if plug_ok else 'NU'} datapack_referit={dp_ok}")

send("datapack list")
time.sleep(5)
txt = get_log()
for l in [l for l in txt.splitlines() if "file/" in l or "enabled" in l.lower()][-10:]:
    log(f"  | {l[:160]}")

# --- selftest ca ExMarius ---
send("execute as ExMarius at @s run function offroader:selftest")
time.sleep(16)
send("scoreboard players get #pass offr.tmp")
time.sleep(3)
send("scoreboard players get #fail offr.tmp")
time.sleep(5)
txt = get_log()
log("--- rezultate selftest din consolă ---")
for l in txt.splitlines()[-40:]:
    if any(k in l for k in ("#pass", "#fail", "Offroader", "offroader", "Unknown", "Expected")):
        log(f"  | {l[:170]}")
log("=== FIX FINALIZAT ===")
