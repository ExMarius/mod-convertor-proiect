#!/usr/bin/env bash
# Deploy la panel.play.hosting (Pterodactyl) — rulat din GitHub Actions.
# Folosire: bash deploy/panel.sh <auto|discover|deploy>
# Necesită env: PTERO_TOKEN (secret GitHub). Opțional: OPS_NAME (nume MC pt. op).
set -o pipefail

MODE="${1:-auto}"
BASE="https://panel.play.hosting"
SRV="$BASE/api/client/servers"
REP="deploy-report"
mkdir -p "$REP"

log() { echo "[deploy] $*"; echo "$*" >> "$REP/jurnal.txt"; }
ok2xx() { case "$1" in 20*) return 0;; *) return 1;; esac; }

if [ -z "${PTERO_TOKEN:-}" ]; then
  log "SECRET LIPSESTE: adaugă PTERO_TOKEN în repo → Settings → Secrets and variables → Actions → New repository secret."
  exit 0
fi

if [ "$MODE" = "auto" ] && [ -f "$REP/DONE.txt" ]; then
  log "Deja deploy-uit (DONE.txt există) — ieșire."
  exit 0
fi

auth=(-H "Authorization: Bearer $PTERO_TOKEN" -H "Accept: application/json")

jget() { # jget <cale-api> <fișier-ieșire>  → tipărește codul HTTP
  curl -sS -m 60 -o "$2" -w '%{http_code}' "${auth[@]}" "$BASE$1"
}
jpost() { # jpost <metodă> <cale-api> <json> [fișier-ieșire]
  local out="${4:-/tmp/api.out}"
  curl -sS -m 60 -o "$out" -w '%{http_code}' -X "$1" "${auth[@]}" \
    -H "Content-Type: application/json" --data "$3" "$BASE$2"
}
enc() { python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))' "$1"; }

# ============================ 1. DISCOVERY ============================
log ""
log "=== $(date -u +%H:%M:%S) DISCOVERY (mod $MODE) ==="

code=$(jget /api/client "$REP/servers.json")
log "GET /api/client → $code"
if ! ok2xx "$code"; then
  log "EROARE: nu pot lista serverele (cod $code)."
  head -c 500 "$REP/servers.json" >> "$REP/jurnal.txt" 2>/dev/null
  exit 1
fi

COUNT=$(jq '.data | length' "$REP/servers.json")
log "Servere pe cont: $COUNT"
if [ "$COUNT" -eq 0 ]; then log "Nu există niciun server pe contul din panel."; exit 1; fi
if [ "$COUNT" -gt 1 ]; then
  log "Mai multe servere — nu ghicesc care. Identificatori: $(jq -r '[.data[].attributes.identifier] | join(", ")' "$REP/servers.json")"
  exit 1
fi

ID=$(jq -r '.data[0].attributes.identifier' "$REP/servers.json")
log "Server selectat: $ID — $(jq -r '.data[0].attributes.name' "$REP/servers.json")"

jget "/api/client/servers/$ID" "$REP/server.json"     >/dev/null
jget "/api/client/servers/$ID/startup" "$REP/startup.json" >/dev/null
jget "/api/client/servers/$ID/resources" "$REP/resources.json" >/dev/null
jget "/api/client/servers/$ID/files/list?directory=%2F" "$REP/files.json" >/dev/null
cp "$REP/server.json" "$REP/server-last.json" 2>/dev/null
cp "$REP/files.json" "$REP/files-last.json" 2>/dev/null

DOCKER=$(jq -r '.attributes.docker_image // "?"' "$REP/server.json")
STATE=$(jq -r '.attributes.current_state // "?"' "$REP/resources.json")
log "imagine docker: $DOCKER"
log "stare curentă: $STATE"
log "variabile startup: $(jq -c '[.data[] | {env: .attributes.env, val: .attributes.server_value}]' "$REP/startup.json")"
log "fișiere root: $(jq -c '[.data[].attributes.name]' "$REP/files.json")"

if jq -e '[.data[].attributes.name] | index("mods") != null' "$REP/files.json" >/dev/null; then
  log "OPRIT: serverul are folder mods/ (Forge/Fabric). Nu pot pune plugin Paper pe el."
  log "Rezolvare: în panel → serverul → Settings/Startup → schimbă egg-ul (Software) în Paper, apoi spune-mi și rulez din nou."
  exit 1
fi

if [ "$MODE" = "discover" ]; then log "Doar discovery (cerut) — gata."; exit 0; fi

# ============================ 2. DEPLOY ============================
log "=== DEPLOY ==="
CHANGED=0

# --- 2a. versiune → 1.21.4 prin variabila egg-ului (dacă există) ---
VERVAR=$(jq -r '[.data[] | select(.attributes.env == "MINECRAFT_VERSION" or .attributes.env == "MC_VERSION") | .attributes.env] | .[0] // empty' "$REP/startup.json")
if [ -n "$VERVAR" ]; then
  OLDVAL=$(jq -r --arg k "$VERVAR" '[.data[] | select(.attributes.env == $k) | .attributes.server_value] | .[0] // "?"' "$REP/startup.json")
  log "Variabilă versiune: $VERVAR = $OLDVAL"
  if [ "$OLDVAL" != "1.21.4" ]; then
    code=$(jpost PUT "/api/client/servers/$ID/startup" "{\"key\":\"$VERVAR\",\"value\":\"1.21.4\"}")
    log "PUT $VERVAR=1.21.4 → $code"
    ok2xx "$code" && CHANGED=1
  fi
  # build pinned pe altă valoare? → latest
  BLDVAR=$(jq -r '[.data[] | select(.attributes.env == "BUILD_VERSION") | .attributes.env] | .[0] // empty' "$REP/startup.json")
  if [ -n "$BLDVAR" ]; then
    BLDVAL=$(jq -r '[.data[] | select(.attributes.env == "BUILD_VERSION") | .attributes.server_value] | .[0] // "?"' "$REP/startup.json")
    if [ "$BLDVAL" != "latest" ]; then
      code=$(jpost PUT "/api/client/servers/$ID/startup" "{\"key\":\"BUILD_VERSION\",\"value\":\"latest\"}")
      log "PUT BUILD_VERSION=latest → $code"; ok2xx "$code" && CHANGED=1
    fi
  fi
else
  log "Fără variabilă de versiune — upload jar Paper manual (mai jos)."
fi

# --- 2b. Java 21 (Paper 1.21.4 cere Java 21+) ---
if ! echo "$DOCKER" | grep -qiE 'java[ _-]?2[1-9]|java_2[1-9]'; then
  DIVAR=$(jq -r '[.data[] | select(.attributes.env == "DOCKER_IMAGE") | .attributes.env] | .[0] // empty' "$REP/startup.json")
  if [ -n "$DIVAR" ]; then
    code=$(jpost PUT "/api/client/servers/$ID/startup" "{\"key\":\"DOCKER_IMAGE\",\"value\":\"ghcr.io/parkervcp/yolks:java_21\"}")
    log "PUT DOCKER_IMAGE=java_21 → $code"; ok2xx "$code" && CHANGED=1
  else
    log "ATENȚIE: imaginea docker ($DOCKER) nu pare Java 21 și nu e setabilă din API — dacă nu pornește, se schimbă din panel."
  fi
fi

# --- 2c. foldere ---
mk() { # mk <nume> <cale-părinte>
  code=$(jpost POST "/api/client/servers/$ID/files/create-folder" "{\"name\":\"$1\",\"path\":\"$2\",\"root\":\"$2\"}")
  log "create-folder $2/$1 → $code"
}
mk "plugins" "/"
mk "world" "/"
mk "datapacks" "/world"

# --- 2d. upload fișiere mici (scriere directă) ---
fwrite() { # fwrite <cale-panel> <fișier-local> → cod HTTP
  local p f code
  p="$(enc "$1")"; f="$2"
  curl -sS -m 180 -o /dev/null -w '%{http_code}' -X POST \
    -H "Authorization: Bearer $PTERO_TOKEN" -H "Content-Type: application/octet-stream" \
    --data-binary "@$f" "$SRV/$ID/files/write?file=$p"
}
fbig() { # fbig <dir-panel> <fișier-local> → cod HTTP (endpoint upload semnat)
  local d f url code
  d="$(enc "$1")"; f="$2"
  code=$(curl -sS -m 60 -o /tmp/up.json -w '%{http_code}' "${auth[@]}" "$SRV/$ID/files/upload?directory=$d")
  ok2xx "$code" || { echo "$code"; return; }
  url=$(jq -r '.attributes.url' /tmp/up.json)
  curl -sS -m 900 -o /dev/null -w '%{http_code}' -F "files[]=@$f" "$url"
}

PLUG="plugin/release/OffroaderPlugin.jar"
DPCK="offroader/release/OffroaderDatapack.zip"
[ -f "$PLUG" ] || { log "Lipsește $PLUG din repo."; exit 1; }
[ -f "$DPCK" ] || { log "Lipsește $DPCK din repo."; exit 1; }

code=$(fwrite "/plugins/OffroaderPlugin.jar" "$PLUG")
log "upload plugins/OffroaderPlugin.jar → $code"
ok2xx "$code" || exit 1
CHANGED=1

code=$(fwrite "/world/datapacks/OffroaderDatapack.zip" "$DPCK")
log "upload world/datapacks/OffroaderDatapack.zip → $code"
ok2xx "$code" || exit 1
CHANGED=1

# --- 2e. jar Paper doar dacă egg-ul NU se auto-descarcă după versiune ---
if [ -z "$VERVAR" ]; then
  JARVAR_VAL=$(jq -r '[.data[] | select(.attributes.env == "SERVER_JARFILE") | .attributes.server_value] | .[0] // empty' "$REP/startup.json")
  TARGET="${JARVAR_VAL:-server.jar}"
  OLDJAR=$(jq -r --arg t "$TARGET" '[.data[].attributes | select(.name == $t) | .name] | .[0] // empty' "$REP/files.json")
  if [ -n "$OLDJAR" ]; then
    code=$(jpost POST "/api/client/servers/$ID/files/rename" "{\"root\":\"/\",\"files\":[{\"from\":\"$OLDJAR\",\"to\":\"$OLDJAR.arena-bak\"}]}")
    log "backup $OLDJAR → $OLDJAR.arena-bak : $code"
  fi
  PURL=$(curl -sfL "https://fill.papermc.io/v3/projects/paper/versions/1.21.4/builds/latest" | jq -r '.downloads["server:default"].url')
  log "descarc Paper 1.21.4 de la: $PURL"
  curl -sfL -o /tmp/paper-1.21.4.jar "$PURL" || { log "download Paper a eșuat"; exit 1; }
  log "upload /$TARGET ($(stat -c%s /tmp/paper-1.21.4.jar) bytes)..."
  code=$(fbig "/" "/tmp/paper-1.21.4.jar")
  log "upload jar → $code"
  ok2xx "$code" || exit 1
  CHANGED=1
fi

# --- 2f. server.properties (backup + patch) ---
PROP=/tmp/server.properties
code=$(curl -sS -m 60 -o "$PROP" -w '%{http_code}' -H "Authorization: Bearer $PTERO_TOKEN" \
  "$SRV/$ID/files/content?file=%2Fserver.properties")
if ok2xx "$code"; then
  log "server.properties existent — backup ca server.properties.arena-bak"
  fwrite "/server.properties.arena-bak" "$PROP" >/dev/null
else
  log "server.properties inexistent ($code) — îl creez proaspăt"
  : > "$PROP"
fi
RPURL="https://github.com/ExMarius/mod-convertor-proiect/raw/arena%2F01a106d2-mod-convertor-proiect/offroader/release/OffroaderResourcePack.zip"
patch_prop() {
  if grep -q "^$1=" "$PROP" 2>/dev/null; then sed -i "s|^$1=.*|$1=$2|" "$PROP"; else echo "$1=$2" >> "$PROP"; fi
}
patch_prop "online-mode" "false"
patch_prop "enforce-secure-profile" "false"
patch_prop "spawn-protection" "0"
patch_prop "resource-pack" "$RPURL"
patch_prop "motd" "Offroader 1:1 — test server"
code=$(fwrite "/server.properties" "$PROP")
log "upload server.properties → $code"
ok2xx "$code" || exit 1
CHANGED=1

# --- 2g. op pentru jucător (UUID offline), dacă s-a dat numele ---
if [ -n "${OPS_NAME:-}" ]; then
  OUUID=$(python3 - "$OPS_NAME" <<'PYEOF'
import hashlib, uuid, sys
name = sys.argv[1]
h = bytearray(hashlib.md5(b"OfflinePlayer:" + name.encode()).digest())
h[6] = (h[6] & 0x0F) | 0x30
h[8] = (h[8] & 0x3F) | 0x80
print(uuid.UUID(bytes=bytes(h)))
PYEOF
)
  printf '[{"uuid":"%s","name":"%s","level":4,"bypassesPlayerLimit":true}]\n' "$OUUID" "$OPS_NAME" > /tmp/ops.json
  code=$(fwrite "/ops.json" "/tmp/ops.json")
  log "upload ops.json (op pentru $OPS_NAME) → $code"
  ok2xx "$code" && CHANGED=1
fi

# --- 2h. restart + verificare din loguri ---
check_log() {
  curl -sS -m 60 -H "Authorization: Bearer $PTERO_TOKEN" -o /tmp/latest.log \
    "$SRV/$ID/files/content?file=%2Flogs%2Flatest.log" 2>/dev/null
  grep -q "OffroaderPlugin activ" /tmp/latest.log 2>/dev/null
}

if [ "$CHANGED" = "1" ]; then
  SIG="restart"
  [ "$STATE" = "offline" ] || [ "$STATE" = "stopped" ] && SIG="start"
  code=$(jpost POST "/api/client/servers/$ID/power" "{\"signal\":\"$SIG\"}")
  log "power: $SIG → $code"
  log "aștept boot-ul serverului (90s)..."
  sleep 90
  if check_log; then
    log "PLUGIN OK — OffroaderPlugin s-a încărcat pe serverul real!"
    { grep -m1 "Starting minecraft server version" /tmp/latest.log; } >> "$REP/jurnal.txt" 2>/dev/null
    date -u > "$REP/DONE.txt"
  else
    log "Încă nu apare în log — mai aștept 60s (poate descarcă Paper la boot)..."
    sleep 60
    if check_log; then
      log "PLUGIN OK — OffroaderPlugin s-a încărcat pe serverul real!"
      { grep -m1 "Starting minecraft server version" /tmp/latest.log; } >> "$REP/jurnal.txt" 2>/dev/null
      date -u > "$REP/DONE.txt"
    else
      log "PLUGIN NU apare în log. Ultimele linii relevante:"
      { grep -iE "offroader|error|exception|starting minecraft|version" /tmp/latest.log 2>/dev/null | head -25; } >> "$REP/jurnal.txt"
      { [ -s /tmp/latest.log ] || echo "(latest.log gol/inaccesibil)"; } >> "$REP/jurnal.txt"
    fi
  fi
  jget "/api/client/servers/$ID/resources" "$REP/resources-after.json" >/dev/null
  log "stare după restart: $(jq -r '.attributes.current_state // "?"' "$REP/resources-after.json")"
else
  log "Nicio schimbare necesară — nu repornesc."
  date -u > "$REP/DONE.txt"
fi

log "=== GATA (mod $MODE) ==="
