#!/usr/bin/env python3
"""Deploy Offroader pe serverul Falix prin API v2 (client.falixnodes.net/api/v2).

Pași: /me → /servers → upload plugin+datapack → proprietăți → restart →
verifică din consolă că pluginul s-a încărcat.
Raport complet în deploy-report/falix-deploy.txt.
"""
import os, sys, json, time, base64
import urllib.request, urllib.error

BASE = "https://client.falixnodes.net/api/v2"
TOKEN = os.environ.get("FALIX_TOKEN", "")
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/falix-deploy.txt", "a", encoding="utf-8")

def log(m):
    print(m)
    LOG.write(m + "\n"); LOG.flush()

def api(method, path, body=None, raw=None, ctype="application/json", timeout=60):
    h = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    data = None
    if raw is not None:
        data = raw; h["Content-Type"] = ctype
    elif body is not None:
        data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8", "ignore")
            try: return r.status, json.loads(txt)
            except Exception: return r.status, {"raw": txt[:400]}
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "ignore")
        try: return e.code, json.loads(txt)
        except Exception: return e.code, {"raw": txt[:400]}
    except Exception as e:
        return 0, {"error": {"code": "network", "message": str(e)}}

log("")
log(f"=== {time.strftime('%H:%M:%S')} DEPLOY FALIX ===")

# 1. /me
code, r = api("GET", "/me")
if code != 200:
    log(f"/me → {code}: {json.dumps(r)[:300]}")
    sys.exit(1)
acc = r.get("data", {}).get("account", {})
scopes = r.get("data", {}).get("key", {}).get("scopes", [])
log(f"cont: {acc.get('username')} (id {acc.get('id')})")
log(f"scopes cheie: {scopes}")

# 2. serverele
code, r = api("GET", "/servers?limit=100")
if code != 200:
    log(f"/servers → {code}: {json.dumps(r)[:300]}"); sys.exit(1)
servers = r.get("data", [])
log(f"servere: {len(servers)}")
SID = None
for s in servers:
    log(f"  • {s.get('name')} (id={s.get('id')}, status={s.get('status')}, "
        f"addr={s.get('address') or s.get('primary_allocation') or '?'}) {json.dumps(s)[:220]}")
if len(servers) == 1:
    SID = servers[0].get("id")
else:
    for s in servers:
        if "uke" in str(s.get("name", "")).lower() or "uke" in json.dumps(s).lower():
            SID = s.get("id"); break
if not SID:
    log("nu știu ce server să aleg — opresc"); sys.exit(1)
log(f"server ales: {SID}")

# 3. structura de fișiere
code, r = api("GET", f"/servers/{SID}/files?path=/")
root_files = []
if code == 200:
    fd = r.get("data", [])
    if isinstance(fd, dict): fd = fd.get("files", fd.get("data", []))
    root_files = [f.get("name") for f in fd if isinstance(f, dict)]
log(f"root: {root_files[:25]}")
world = "world" if "world" in root_files else next((f for f in root_files if f in ("world", "World", "main", "survival")), "world")
log(f"lumea: {world}")

# 4. upload (încearcă PUT content raw → base64 → SFTP)
def put_file(path, local):
    blob = open(local, "rb").read()
    log(f"upload {path} ({len(blob)} bytes)...")
    # a) raw octet-stream
    code, r = api("PUT", f"/files/content?path={urllib.parse.quote(path)}", raw=blob,
                  ctype="application/octet-stream")
    if code in (200, 201, 204):
        log(f"  OK (raw): {json.dumps(r)[:120]}"); return True
    log(f"  raw → {code}: {json.dumps(r)[:200]}")
    # b) JSON cu base64
    code, r = api("PUT", f"/files/content", body={"path": path, "content": base64.b64encode(blob).decode()})
    if code in (200, 201, 204):
        log(f"  OK (base64): {json.dumps(r)[:120]}"); return True
    log(f"  base64 → {code}: {json.dumps(r)[:200]}")
    # c) JSON cu text?
    code, r = api("PUT", f"/files/content", body={"path": path, "content": base64.b64encode(blob).decode(), "encoding": "base64"})
    if code in (200, 201, 204):
        log(f"  OK (b64+enc): {json.dumps(r)[:120]}"); return True
    log(f"  b64+enc → {code}: {json.dumps(r)[:200]}")
    return False

import urllib.parse  # noqa

ok_plugin = put_file("plugins/OffroaderPlugin.jar", "plugin/release/OffroaderPlugin.jar")
ok_dp = put_file(f"{world}/datapacks/OffroaderDatapack.zip", "offroader/release/OffroaderDatapack.zip")

if not (ok_plugin and ok_dp):
    log("upload prin API a eșuat — încerc SFTP...")
    code, r = api("GET", f"/servers/{SID}/sftp")
    log(f"/sftp → {code}: {json.dumps(r)[:400]}")
    if code == 200:
        d = r.get("data", {})
        host = d.get("host") or d.get("hostname"); port = int(d.get("port", 22))
        user = d.get("username") or d.get("user"); pw = d.get("password")
        try:
            import paramiko
            c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(host, port=port, username=user, password=pw, timeout=20,
                      allow_agent=False, look_for_keys=False)
            sftp = c.open_sftp()
            for p, l in [("plugins/OffroaderPlugin.jar", "plugin/release/OffroaderPlugin.jar"),
                         (f"{world}/datapacks/OffroaderDatapack.zip", "offroader/release/OffroaderDatapack.zip")]:
                sftp.put(l, p); log(f"  SFTP OK: {p} ({sftp.stat(p).st_size} b)")
            ok_plugin = ok_dp = True
            sftp.close(); c.close()
        except Exception as e:
            log(f"  SFTP eșuat: {type(e).__name__}: {e}")
    else:
        sys.exit(1)

# 5. proprietăți: resource-pack
RP = "https://github.com/ExMarius/mod-convertor-proiect/raw/arena%2F01a106d2-mod-convertor-proiect/offroader/release/OffroaderResourcePack.zip"
code, r = api("PUT", f"/servers/{SID}/properties", body={"properties": {"resource-pack": RP}})
log(f"properties resource-pack → {code}: {json.dumps(r)[:200]}")
if code not in (200, 201, 204):
    code, r = api("PUT", f"/servers/{SID}/properties", body={"resource-pack": RP})
    log(f"properties (formă 2) → {code}: {json.dumps(r)[:200]}")

# 6. restart
code, r = api("POST", f"/servers/{SID}/power", body={"signal": "restart"})
log(f"power restart → {code}: {json.dumps(r)[:300]}")
if code == 403 and "action_url" in json.dumps(r):
    log("!! Este nevoie de verificare în browser — dă-mi URL-ul asta:")
    log(json.dumps(r.get("error", {}).get("action_url") or r, ensure_ascii=False))
    sys.exit(2)

# 7. așteaptă boot-ul + caut pluginul în consolă
found = False
for i in range(30):
    time.sleep(6)
    code, r = api("GET", f"/servers/{SID}/console/log")
    if code == 200:
        d = r.get("data")
        text = d if isinstance(d, str) else json.dumps(d)
        if "OffroaderPlugin activ" in text:
            found = True
            tail = [l for l in text.splitlines() if "Offroader" in l or "Done (" in l][:8]
            for l in tail: log(f"  | {l[:160]}")
            break
        if "Enabling OffroaderPlugin" in text:
            found = True
            break
log(f"plugin în consolă: {'DA ✓' if found else 'NU (verifică manual)'}")
log("=== DEPLOY FALIX FINALIZAT ===")
