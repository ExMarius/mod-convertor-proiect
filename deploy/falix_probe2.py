#!/usr/bin/env python3
"""Auto-discovery API Falix: DNS candidates + grep prin JS-ul panelului."""
import os, sys, re, json
import urllib.request, urllib.error, socket

TOKEN = os.environ.get("FALIX_TOKEN", "")

def get(url, timeout=20, binary=False):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0",
        "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return 0, str(e).encode()

print("=== 1. DNS candidates ===")
CANDS = ["api.falix.gg", "api.falixserver.net", "api.falixnodes.com", "api.falix.net",
         "falix.gg", "api.falixnodes.net", "api.client.falixnodes.net",
         "api.falixservers.net", "api.falixcloud.net"]
for c in CANDS:
    try:
        ip = socket.gethostbyname(c)
        print(f"  {c:32} → {ip}")
    except Exception:
        pass

print("\n=== 2. JS-ul panelului (client.falixnodes.net) ===")
code, html = get("https://client.falixnodes.net/")
print(f"  panel HTML: {code} ({len(html)} bytes)")
scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html.decode("utf-8", "ignore"))
print(f"  scripturi: {scripts[:8]}")
found = set()
for s in scripts[:10]:
    url = s if s.startswith("http") else "https://client.falixnodes.net" + (s if s.startswith("/") else "/" + s)
    code, js = get(url, timeout=30)
    if code != 200 or not js:
        continue
    js = js.decode("utf-8", "ignore")
    print(f"  bundle {url.split('/')[-1][:40]}: {len(js)} bytes")
    # caută orice URL cu falix / api
    for m in re.findall(r'https?://[a-zA-Z0-9.-]*falix[a-zA-Z0-9.-]*[^\s"\'`]*', js):
        found.add(m[:120])
    for m in re.findall(r'https?://api\.[a-zA-Z0-9.-]+[^\s"\'`]*', js):
        found.add(m[:120])
    # și mențiuni flx_live / Authorization
    if "flx_live" in js:
        print("  >>> bundle conține 'flx_live'!")
        for m in re.findall(r'.{60}flx_live.{60}', js):
            print(f"      context: {m}")
print("\n  URL-uri API găsite în JS:")
for f in sorted(found):
    print(f"    {f}")

print("\n=== 3. probăm bazele găsite cu tokenul ===")
bases = sorted(set(re.match(r'https?://[^/]+', f).group(0) for f in found if "api" in f))
for b in bases[:6]:
    for p in ["/", "/servers", "/me", "/user", "/docs", "/openapi.json"]:
        code, body = get(b + p)
        body = (body or b"")[:200]
        try: body = body.decode("utf-8", "ignore")
        except Exception: body = str(body)
        if code not in (0, 404):
            # probăm și cu auth
            req = urllib.request.Request(b + p, headers={
                "Authorization": f"Bearer {TOKEN}", "Accept": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    print(f"  {b}{p} → {r.status}: {r.read(200).decode('utf-8','ignore')}")
            except urllib.error.HTTPError as e:
                print(f"  {b}{p} → anonim:{code}, auth:{e.code}: {e.read(150).decode('utf-8','ignore')}")
            except Exception as e2:
                print(f"  {b}{p} → anonim:{code}, auth err: {e2}")
            break  # prima cale care răspunde la această bază
