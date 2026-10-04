#!/usr/bin/env bash
# Pregătește un server Paper 1.21.4 local (în sandbox) cu pluginul + datapackul offroader.
# Usage: bash deploy/server_local.sh [dir]  (implicit /tmp/mcserver)
set -e
DIR="${1:-/tmp/mcserver}"
JAVA_BIN="${JAVA_BIN:-/usr/local/lib/python3.11/dist-packages/jdk4py/java-runtime/bin/java}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

[ -x "$JAVA_BIN" ] || { echo "java lipsă: $JAVA_BIN (pip3 install jdk4py)"; exit 1; }
if [ -f "$REPO/server/paper-1.21.4.jar" ]; then
  cp "$REPO/server/paper-1.21.4.jar" "$DIR/paper.jar"
elif [ ! -f "$DIR/paper.jar" ]; then
  echo "lipsește paper.jar (nici în repo, nici în $DIR)"; exit 1
fi
[ -f "$REPO/plugin/release/OffroaderPlugin.jar" ] || { echo "lipsește plugin/release/OffroaderPlugin.jar (CI build-plugin)"; exit 1; }

mkdir -p "$DIR/plugins" "$DIR/world/datapacks"
cp "$REPO/plugin/release/OffroaderPlugin.jar" "$DIR/plugins/"
cp "$REPO/offroader/release/OffroaderDatapack.zip" "$DIR/world/datapacks/"

echo "eula=true" > "$DIR/eula.txt"

RP="https://github.com/ExMarius/mod-convertor-proiect/raw/arena%2F01a106d2-mod-convertor-proiect/offroader/release/OffroaderResourcePack.zip"
if [ ! -f "$DIR/server.properties" ]; then
  cat > "$DIR/server.properties" <<EOF
server-port=25565
online-mode=false
enforce-secure-profile=false
rcon=true
rcon.port=25575
rcon.password=arena-rcon
level-type=minecraft\\:flat
generate-structures=false
spawn-monsters=false
difficulty=peaceful
view-distance=6
simulation-distance=6
max-players=5
motd=Offroader 1:1 — test server
resource-pack=$RP
spawn-protection=0
white-list=false
EOF
fi

echo "Gata. Pornește cu:"
echo "  cd $DIR && $JAVA_BIN -Xms512M -Xmx2G -jar paper.jar nogui"
