#!/usr/bin/env python3
"""Punte OAuth pentru mcp.ouipanel.com (MCP-ul OuiPanel), fără browser.

Flux:
  begin   → discovery + înregistrare dinamică client + generează linkul de aprobare
            (deploy-report/authorize-url.txt) și salvează starea PKCE criptat
            (deploy/oauth-state.enc, cheie = PTERO_TOKEN din GitHub Secrets).
  finish  → citește deploy/callback.txt (URL-ul lipit de user după aprobare),
            schimbă codul pe token-uri, le salvează criptat (deploy/mcp-tokens.enc).
  token   → tipărește access token valid (reîmprospătează la nevoie) pentru workflow.

De ce așa: documentația OuiPanel spune că un client fără browser nu poate face
consimțământul OAuth. Noi îl separam: browserul e al userului (pasul de aprobare),
restul îl face CI-ul. Cheia de criptare e un secret GitHub, deci fișierele
comise public sunt sigure.
"""
import os, sys, json, base64, hashlib, secrets, subprocess, time
import urllib.request, urllib.parse, urllib.error

ORIGIN = "https://mcp.ouipanel.com"
MCP_URL = ORIGIN + "/mcp"
REDIRECT = "http://localhost:8931/callback"
KEY = os.environ.get("PTERO_TOKEN", "").strip()
STATE_FILE = "deploy/oauth-state.enc"
TOK_FILE = "deploy/mcp-tokens.enc"
REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/jurnal-oauth.txt", "a", encoding="utf-8")

def log(m):
    print(f"[oauth] {m}")
    LOG.write(m + "\n")
    LOG.flush()

def http(method, url, data=None, form=None, headers=None):
    hdrs = {"User-Agent": "arena-agent/1.0", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        hdrs["Content-Type"] = "application/json"
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8", "ignore"), dict(r.headers)
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", "ignore"), dict(e.headers)
        except Exception:
            return e.code, "", {}
    except Exception as e:
        return 0, str(e), {}

def enc_json(obj):
    if not KEY:
        raise SystemExit("PTERO_TOKEN lipsește — nu pot cripta.")
    p = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-base64", "-k", KEY],
        input=json.dumps(obj).encode(), capture_output=True, check=True)
    return p.stdout.decode()

def dec_json(path):
    if not os.path.exists(path):
        return None
    p = subprocess.run(
        ["openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-base64", "-k", KEY],
        input=open(path, "rb").read(), capture_output=True)
    if p.returncode != 0:
        return None
    try:
        return json.loads(p.stdout.decode())
    except Exception:
        return None

def b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

def discover():
    """RFC 8414 + varianta MCP (protected-resource). Returnează endpoint-urile."""
    for path in ["/.well-known/oauth-authorization-server",
                 "/.well-known/oauth-protected-resource"]:
        code, body, _ = http("GET", ORIGIN + path)
        log(f"GET {path} → {code}: {body[:220]}")
        if code != 200:
            continue
        try:
            meta = json.loads(body)
        except Exception:
            continue
        if "authorization_servers" in meta:
            for srv in meta["authorization_servers"]:
                c2, b2, _ = http("GET", srv.rstrip("/") + "/.well-known/oauth-authorization-server")
                log(f"GET {srv}/.well-known/... → {c2}: {b2[:220]}")
                if c2 == 200:
                    try:
                        return json.loads(b2)
                    except Exception:
                        pass
            return None
        if meta.get("authorization_endpoint") and meta.get("token_endpoint"):
            return meta
    return None

def cmd_begin():
    meta = discover()
    if not meta:
        log("discovery a eșuat — endpoint-uri OAuth negăsite. Opresc.")
        return 1
    auth_ep, tok_ep = meta["authorization_endpoint"], meta["token_endpoint"]
    reg_ep = meta.get("registration_endpoint", "")
    log(f"authorize: {auth_ep}")
    log(f"token:     {tok_ep}")
    log(f"register:  {reg_ep or '(lipsă)'}")

    client_id = ""
    if reg_ep:
        code, body, _ = http("POST", reg_ep, data={
            "client_name": "arena-agent (ExMarius)",
            "redirect_uris": [REDIRECT],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        })
        log(f"POST register → {code}: {body[:400]}")
        if code in (200, 201):
            try:
                client_id = json.loads(body).get("client_id", "")
            except Exception:
                pass
    if not client_id:
        log("înregistrare dinamică indisponibilă/refuzată — nu pot continua fără client_id.")
        return 1

    verifier = b64url(secrets.token_bytes(48))
    challenge = b64url(hashlib.sha256(verifier.encode()).digest())
    q = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": "arena",
        "resource": MCP_URL,
    })
    url = auth_ep + ("&" if "?" in auth_ep else "?") + q
    with open(f"{REP}/authorize-url.txt", "w") as f:
        f.write(url + "\n")
    with open(STATE_FILE, "w") as f:
        f.write(enc_json({
            "verifier": verifier, "client_id": client_id,
            "token_endpoint": tok_ep, "redirect": REDIRECT,
        }))
    log("LINK DE APROBARE GENERAT → deploy-report/authorize-url.txt")
    log("Pasul următor (user): deschide linkul, alege serverul + permisiunile, aprobă,")
    log("apoi copiază URL-ul complet din bara browserului (începe cu http://localhost:8931/...)")
    log("și lipește-l în chat.")
    return 0

def cmd_finish():
    st = dec_json(STATE_FILE)
    if not st:
        log("lipsă/decriptare eșuată pentru oauth-state.enc — rulează begin întâi.")
        return 1
    cb = ""
    if os.path.exists("deploy/callback.txt"):
        cb = open("deploy/callback.txt").read().strip()
    if not cb:
        log("lipsă deploy/callback.txt — comite URL-ul de callback de la user.")
        return 1
    q = urllib.parse.parse_qs(urllib.parse.urlparse(cb).query)
    if "code" not in q:
        log(f"callback fără cod: {cb[:250]}")
        if "error" in q:
            log(f"eroare OAuth: {q.get('error_description', q.get('error'))}")
        return 1
    code, body, _ = http("POST", st["token_endpoint"], form={
        "grant_type": "authorization_code",
        "code": q["code"][0],
        "redirect_uri": st["redirect"],
        "code_verifier": st["verifier"],
        "client_id": st["client_id"],
    })
    log(f"POST token → {code}: {body[:400]}")
    if code != 200:
        return 1
    tok = json.loads(body)
    tok["_ts"] = time.time()
    tok["_client_id"] = st["client_id"]
    tok["_token_endpoint"] = st["token_endpoint"]
    with open(TOK_FILE, "w") as f:
        f.write(enc_json(tok))
    os.remove(STATE_FILE)
    if os.path.exists("deploy/callback.txt"):
        os.remove("deploy/callback.txt")
    log("TOKEN-URI SALVATE criptat → deploy/mcp-tokens.enc ( acces: da / refresh: da )")
    return 0

def cmd_token():
    tok = dec_json(TOK_FILE)
    if not tok:
        log("fără token-uri salvate — rulează begin + finish întâi.")
        return 1
    ttl = int(tok.get("expires_in") or 3600)
    if time.time() - tok.get("_ts", 0) > max(ttl - 120, 0):
        log("access token expirat — refresh...")
        code, body, _ = http("POST", tok["_token_endpoint"], form={
            "grant_type": "refresh_token",
            "refresh_token": tok.get("refresh_token", ""),
            "client_id": tok.get("_client_id", ""),
        })
        log(f"POST refresh → {code}")
        if code == 200:
            new = json.loads(body)
            tok.update({k: v for k, v in new.items() if not k.startswith("_")})
            tok["_ts"] = time.time()
            with open(TOK_FILE, "w") as f:
                f.write(enc_json(tok))
        else:
            log(f"refresh eșuat: {body[:300]}")
            return 1
    sys.stdout.write(tok.get("access_token", ""))
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "begin"
    sys.exit({"begin": cmd_begin, "finish": cmd_finish, "token": cmd_token}.get(cmd, lambda: (log("comandă necunoscută"), 1)[1])())
