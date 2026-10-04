#!/usr/bin/env python3
"""Client MCP minimal (streamable HTTP) pentru dash.ouipanel.com/mcp.

Rulează din GitHub Actions (CI are internet complet; sandbox-ul nu).
Usage:
  MCP_URL="https://dash.ouipanel.com/mcp?token=..." [MCP_TOKEN="..."] \
    OPS_NAME="NumeMC" python3 deploy/mcp_client.py [discover|tools|call <nume> '<json>']

Scrie raportul în deploy-report/jurnal-mcp.txt.
"""
import os, sys, json
import urllib.request, urllib.parse, urllib.error

REP = "deploy-report"
os.makedirs(REP, exist_ok=True)
LOG = open(f"{REP}/jurnal-mcp.txt", "a", encoding="utf-8")

def log(m):
    print(f"[mcp] {m}")
    LOG.write(m + "\n")
    LOG.flush()

URL = os.environ.get("MCP_URL", "").strip()
TOKEN = os.environ.get("MCP_TOKEN", "").strip()

if not URL:
    log("MCP_URL lipsește — adaugă secretul MCP_URL (linkul complet de pe pagina /mcp din panel).")
    sys.exit(0)

# token ascuns în URL (?token=... sau #...) → îl folosim și ca Bearer
_u = urllib.parse.urlparse(URL)
_q = urllib.parse.parse_qs(_u.query)
if not TOKEN:
    TOKEN = _q.get("token", _q.get("key", [None]))[0] or ""
    if not TOKEN and _u.fragment:
        _f = urllib.parse.parse_qs(_u.fragment)
        TOKEN = (_f.get("token", [None]) or [None])[0] or ""

SESSION = {"id": None}
_next_id = [0]

def rpc(method, params=None, notify=False):
    """un request JSON-RPC; suportă răspuns JSON sau SSE (data: {...})"""
    _next_id[0] += 1
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        body["params"] = params
    if not notify:
        body["id"] = _next_id[0]
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "arena-agent/1.0",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if SESSION["id"]:
        headers["Mcp-Session-Id"] = SESSION["id"]
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            sid = r.headers.get("Mcp-Session-Id")
            if sid:
                SESSION["id"] = sid
            raw = r.read().decode("utf-8", "ignore")
            status = r.status
    except urllib.error.HTTPError as e:
        raw = ""
        try:
            raw = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        log(f"HTTP {e.code} la {method}: {raw[:400]}")
        if e.code in (401, 403):
            log("Token invalid/lipsă sau MCP dezactivat în panel — verifică pagina /mcp.")
        return None
    except Exception as e:
        log(f"eroare rețea la {method}: {e}")
        return None
    # răspuns: JSON simplu sau evenimente SSE
    for line in raw.splitlines():
        if line.startswith("data:"):
            try:
                return json.loads(line[5:].strip())
            except Exception:
                pass
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw[:2000], "status": status}

log("")
log(f"=== MCP {sys.argv[1] if len(sys.argv) > 1 else 'discover'} → {URL.split('?')[0]} ===")

# 1. initialize (handshake)
r = rpc("initialize", {
    "protocolVersion": "2025-03-26",
    "capabilities": {},
    "clientInfo": {"name": "arena-agent", "version": "1.0"},
})
if not r or "result" not in (r or {}):
    log(f"initialize a eșuat: {json.dumps(r)[:400] if r else 'fără răspuns'}")
    log("Dacă e 401/403: token greșit. Dacă pagina /mcp oferă doar OAuth (butone 'Connect'), spune-mi — mergem pe SFTP.")
    sys.exit(1)
server_info = r["result"].get("serverInfo", {})
log(f"conectat la: {server_info.get('name','?')} v{server_info.get('version','?')} "
    f"(protocol {r['result'].get('protocolVersion','?')})")
rpc("notifications/initialized", notify=True)

cmd = sys.argv[1] if len(sys.argv) > 1 else "discover"

if cmd in ("discover", "tools", "auto"):
    r = rpc("tools/list")
    tools = (r or {}).get("result", {}).get("tools", [])
    log(f"tools/list → {len(tools)} unelte disponibile:")
    for t in tools:
        log(f"  • {t.get('name','?')} — {str(t.get('description',''))[:200]}")
        props = (t.get("inputSchema") or {}).get("properties") or {}
        if props:
            log(f"      argumente: {json.dumps({k: v.get('type','?') for k, v in props.items()})}")
    if cmd == "auto":
        log("(mod auto: deocamdată doar inventarul de unelte — deploy-ul vine imediat ce văd ce știe panelul)")

elif cmd == "call":
    name = sys.argv[2]
    args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    r = rpc("tools/call", {"name": name, "arguments": args})
    out = json.dumps(r, ensure_ascii=False)[:6000] if r else "fără răspuns"
    log(f"tools/call {name} {json.dumps(args, ensure_ascii=False)[:300]} →")
    if r and "result" in r:
        for c in (r["result"].get("content") or []):
            if c.get("type") == "text":
                for line in c.get("text", "").splitlines()[:60]:
                    log(f"  | {line}")
        log(f"  (isError={r['result'].get('isError', False)})")
    else:
        log(out)

else:
    log(f"comandă necunoscută: {cmd}")

log("=== GATA ===")
