"""
Ridică un server Minecraft oficial (default: 26.3) în ~/.cache/mc-server,
cu RCON activ, lume flat și datapack-ul Offroader deja instalat.

  python3 setup_server.py [versiune]

Pași:
  1. version_manifest_v2.json (piston-meta) → URL-ul versiunii
  2. JSON-ul versiunii → javaVersion.major + server.jar (cu verificare SHA1)
  3. JRE Temurin de la Adoptium → ~/.cache/mc-server/java/
  4. eula.txt + server.properties (RCON port 25575, parola „offr-test")
  5. world/datapacks/OffroaderDatapack.zip (din offroader/release/)
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

VERSIUNE = sys.argv[1] if len(sys.argv) > 1 else "1.21.4"
HOME = os.path.expanduser("~")
MC = os.path.join(HOME, ".cache", "mc-server")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DP_ZIP = os.path.join(REPO, "offroader", "release", "OffroaderDatapack.zip")
RCON_PORT = 25575
RCON_PW = "offr-test"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def download(url, dest, sha1=None):
    if os.path.exists(dest) and (sha1 is None or sha1_of(dest) == sha1):
        print(f"  deja descărcat: {os.path.basename(dest)}")
        return
    print(f"  descarc {url}")
    data = get(url)
    with open(dest, "wb") as f:
        f.write(data)
    if sha1 and sha1_of(dest) != sha1:
        raise RuntimeError(f"SHA1 mismatch pentru {dest}")


def sha1_of(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(MC, exist_ok=True)

    print(f"[1/5] caut versiunea {VERSIUNE} în manifestul Mojang...")
    manifest = json.loads(get(
        "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"))
    entry = next((v for v in manifest["versions"] if v["id"] == VERSIUNE), None)
    if entry is None:
        entry = next(v for v in manifest["versions"] if v["id"] == manifest["latest"]["release"])
        print(f"  {VERSIUNE} nu există, folosesc ultima versiune: {entry['id']}")
    ver = json.loads(get(entry["url"]))
    java_major = ver.get("javaVersion", {}).get("majorVersion", 21)
    srv = ver["downloads"]["server"]
    print(f"  versiune {entry['id']}, Java {java_major}+, "
          f"server.jar {srv['size']/1e6:.1f} MB")

    print("[2/5] descarc server.jar...")
    download(srv["url"], os.path.join(MC, "server.jar"), srv.get("sha1"))

    java_bin = os.path.join(MC, "java", "bin", "java")
    if not os.path.exists(java_bin):
        print(f"[3/5] descarc JRE {java_major} (Adoptium Temurin)...")
        url = (f"https://api.adoptium.net/v3/binary/latest/{java_major}/ga/"
               f"linux/x64/jre/hotspot/normal/eclipse")
        tgz = os.path.join(MC, "jre.tar.gz")
        download(url, tgz)
        with tarfile.open(tgz) as t:
            top = t.getmembers()[0].name.split("/")[0]
            t.extractall(MC, filter="data")
        os.rename(os.path.join(MC, top), os.path.join(MC, "java"))
        os.remove(tgz)
    else:
        print("[3/5] JRE deja prezent")
    r = subprocess.run([java_bin, "-version"], capture_output=True, text=True)
    print("  " + (r.stderr or r.stdout).splitlines()[0])

    print("[4/5] eula + server.properties...")
    with open(os.path.join(MC, "eula.txt"), "w") as f:
        f.write("eula=true\n")
    with open(os.path.join(MC, "server.properties"), "w") as f:
        f.write(f"""enable-rcon=true
rcon.port={RCON_PORT}
rcon.password={RCON_PW}
level-type=minecraft\\:flat
generate-structures=false
online-mode=false
spawn-protection=0
view-distance=4
simulation-distance=4
spawn-monsters=false
motd=Offroader test
sync-chunk-writes=false
enforce-secure-profile=false
""")

    print("[5/5] instalez datapack-ul în world/datapacks/...")
    dpdir = os.path.join(MC, "world", "datapacks")
    os.makedirs(dpdir, exist_ok=True)
    shutil.copyfile(DP_ZIP, os.path.join(dpdir, "OffroaderDatapack.zip"))
    print("  copiat", os.path.basename(DP_ZIP))

    print(f"\nGata. Pornește serverul din {MC} cu:")
    print(f"  {java_bin} -Xms512M -Xmx1200M -jar server.jar nogui")


if __name__ == "__main__":
    main()
