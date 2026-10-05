#!/usr/bin/env python3
"""Deploy prin SFTP pe serverul Pterodactyl (FĂRĂ Cloudflare — TCP direct).

Funcționează din sandbox sau din GitHub Actions (CI).
Usage:
  SFTP_CREDS="user@host:port:parolă" [OPS_NAME="NumeMC"] python3 deploy/sftp.py [auto|discover|deploy]
sau variabile separate: SFTP_HOST, SFTP_PORT, SFTP_USER, SFTP_PASS.
"""
import os, sys, re, json

REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/jurnal-sftp.txt", "a", encoding="utf-8")

def log(msg):
    print(f"[sftp] {msg}")
    LOG.write(msg + "\n")
    LOG.flush()

creds = os.environ.get("SFTP_CREDS", "")
if creds:
    user, rest = creds.split("@", 1)
    host, rest = rest.split(":", 1)
    port, pw = rest.split(":", 1)
    os.environ.update(SFTP_USER=user, SFTP_HOST=host, SFTP_PORT=port, SFTP_PASS=pw)

HOST = os.environ.get("SFTP_HOST", "")
PORT = int(os.environ.get("SFTP_PORT", "2022") or 2022)
USER = os.environ.get("SFTP_USER", "")
PW = os.environ.get("SFTP_PASS", "")
MODE = sys.argv[1] if len(sys.argv) > 1 else "auto"
OPS = os.environ.get("OPS_NAME", "")

if not (HOST and USER and PW):
    log("CREDENȚIALE SFTP LIPSESC — setează SFTP_CREDS=user@host:port:parolă.")
    sys.exit(0)

try:
    import paramiko
except ImportError:
    log("pip install paramiko ...")
    os.system("pip3 install -q paramiko")
    import paramiko

log("")
log(f"=== SFTP {MODE} — conectez la {USER}@{HOST}:{PORT} ===")
cl = paramiko.SSHClient()
cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cl.connect(HOST, port=PORT, username=USER, password=PW,
           timeout=30, allow_agent=False, look_for_keys=False)
sftp = cl.open_sftp()
log("CONEXIUNE SFTP OK")

def ls(path="/"):
    try:
        return sorted(e.filename for e in sftp.listdir_attr(path))
    except IOError as e:
        log(f"ls {path}: {e}")
        return []

root = ls("/")
log(f"fișiere root: {root}")
has_mods = "mods" in root
has_plugins = "plugins" in root
has_world = "world" in root
log(f"mods={has_mods} plugins={has_plugins} world={has_world}")

ver = "?"
paper_info = []
try:
    with sftp.open("/logs/latest.log") as f:
        head = f.read(400000).decode("utf-8", "ignore")
    m = re.search(r"Starting minecraft server version ([0-9.]+)", head)
    if m:
        ver = m.group(1)
    paper_info = [l for l in head.splitlines()
                  if re.search(r"(?i)offroader|paper|forge|fabric|error|exception", l)][:12]
    log(f"versiune din logs/latest.log: {ver}")
    for l in paper_info:
        log(f"  | {l[:160]}")
except IOError:
    log("fără logs/latest.log (server nou / never started?)")

if has_mods:
    log("OPRIT: serverul are folder mods/ (Forge/Fabric) — pluginul Paper nu poate rula pe el.")
    log("Rezolvare: panel → serverul → Settings/Startup → schimbă Software/Egg în Paper 1.21.4, apoi repornește deploy-ul.")
    sys.exit(1)

if MODE == "discover":
    log("doar discovery — gata.")
    sys.exit(0)

# ------------------------------ DEPLOY ------------------------------
def mkdirs(path):
    cur = ""
    for p in path.strip("/").split("/"):
        cur += "/" + p
        try:
            sftp.stat(cur)
        except IOError:
            try:
                sftp.mkdir(cur)
                log(f"mkdir {cur}")
            except IOError as e:
                log(f"mkdir {cur}: {e}")

mkdirs("/plugins")
mkdirs("/world/datapacks")

def put(local, remote):
    sftp.put(local, remote)
    st = sftp.stat(remote)
    log(f"upload {remote} — {st.st_size} bytes")

put("plugin/release/OffroaderPlugin.jar", "/plugins/OffroaderPlugin.jar")
put("offroader/release/OffroaderDatapack.zip", "/world/datapacks/OffroaderDatapack.zip")

# --- server.properties (backup + patch) ---
txt = ""
try:
    with sftp.open("/server.properties") as f:
        txt = f.read().decode("utf-8", "ignore")
    log("server.properties existent — backup ca server.properties.arena-bak")
    try:
        with sftp.open("/server.properties.arena-bak", "w") as f:
            f.write(txt)
    except IOError as e:
        log(f"backup eșuat: {e}")
except IOError:
    log("server.properties inexistent — îl creez")

lines = [l for l in txt.splitlines() if "=" in l or l.strip()]

def setp(key, val):
    for i, l in enumerate(lines):
        if l.startswith(key + "="):
            lines[i] = f"{key}={val}"
            return
    lines.append(f"{key}={val}")

RP = "https://github.com/ExMarius/mod-convertor-proiect/raw/arena%2F01a106d2-mod-convertor-proiect/offroader/release/OffroaderResourcePack.zip"
setp("online-mode", "false")
setp("enforce-secure-profile", "false")
setp("spawn-protection", "0")
setp("resource-pack", RP)
setp("motd", "Offroader 1:1 — test server")
with sftp.open("/server.properties", "w") as f:
    f.write("\n".join(lines) + "\n")
log("server.properties actualizat: online-mode=false, resource-pack automat la conectare")

# --- op pentru jucător (UUID offline-mode) ---
if OPS:
    import hashlib, uuid
    h = bytearray(hashlib.md5(b"OfflinePlayer:" + OPS.encode()).digest())
    h[6] = (h[6] & 0x0F) | 0x30
    h[8] = (h[8] & 0x3F) | 0x80
    u = str(uuid.UUID(bytes=bytes(h)))
    with sftp.open("/ops.json", "w") as f:
        f.write(json.dumps([{"uuid": u, "name": OPS, "level": 4,
                             "bypassesPlayerLimit": True}], indent=2))
    log(f"ops.json scris — op pentru {OPS} (uuid offline: {u})")
else:
    log("fără OPS_NAME — nu scriu ops.json (jucătorul nu va putea da comenzi!)")

log("DEPLOY SFTP GATA.")
log(f"ATENȚIE: versiune detectată = {ver}. Dacă nu e 1.21.4, pluginul/datapack-ul nu se încarcă corect — spune-mi.")
log("REPORNEȘTE serverul din panel (Start/Restart) și intră cu TLauncher (online-mode=false e setat).")
