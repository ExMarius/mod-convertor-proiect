"""
Validează și împachetează datapack-ul și resource pack-ul Offroader.

  python3 build_packs.py           -> validează + ZIP în offroader/release/
  python3 build_packs.py --regen   -> re-rulează toate generatoarele înainte

Verificări:
  - JSON-uri valide (pack.mcmeta, tags, models, items, sounds.json)
  - echilibru {}/[] și ghilimele în .mcfunction
  - orice „function offroader:..." referențiat există ca fișier
  - macrouri ($...) conțin $(...)
  - texturile referențiate de modele există
  - sunetele din sounds.json există ca .ogg
"""
import json
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DP = os.path.join(ROOT, "datapack")
RP = os.path.join(ROOT, "resourcepack")
REL = os.path.join(ROOT, "release")

ERRORS = []


def err(msg):
    ERRORS.append(msg)
    print("EROARE:", msg)


def ok(msg):
    print("  ok:", msg)


# ---------------------------------------------------------------------------
def regen():
    for script in ("gen_textures.py", "gen_model.py", "gen_quats.py",
                   "gen_layout.py", "gen_sounds.py"):
        print(f"-> regen {script}")
        r = subprocess.run([sys.executable, script], cwd=HERE,
                           capture_output=True, text=True)
        if r.returncode != 0:
            err(f"{script} a eșuat:\n{r.stderr}")
            return False
    return True


# ---------------------------------------------------------------------------
def check_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
        return True
    except Exception as e:
        err(f"JSON invalid: {path}: {e}")
        return False


def validate_mcfunctions():
    funcs = {}
    fdir = os.path.join(DP, "data", "offroader", "function")
    for dirpath, _, files in os.walk(fdir):
        for fn in files:
            if not fn.endswith(".mcfunction"):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, fdir)[:-len(".mcfunction")].replace(os.sep, "/")
            funcs[f"offroader:{rel}"] = full

    known_verbs = ("scoreboard", "execute", "give", "summon", "tp", "kill",
                   "playsound", "title", "tellraw", "data", "function",
                   "attribute", "ride", "return", "tag", "say", "setblock",
                   "particle", "stopsound", "effect", "clear", "fill")
    referenced = set()
    for name, path in funcs.items():
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.rstrip("\n")
                if not line or line.lstrip().startswith("#"):
                    continue
                if line.count("{") != line.count("}"):
                    err(f"{name}:{i} acolade dezechilibrate: {line[:90]}")
                if line.count("[") != line.count("]"):
                    err(f"{name}:{i} paranteze drepte dezechilibrate: {line[:90]}")
                if line.count('"') % 2:
                    err(f"{name}:{i} ghilimele impare: {line[:90]}")
                body = line
                if body.startswith("$"):
                    if "$(" not in body:
                        err(f"{name}:{i} macro fără $(): {line[:90]}")
                    body = body[1:]
                verb = body.split(" ", 1)[0]
                if verb not in known_verbs:
                    err(f"{name}:{i} verb necunoscut «{verb}»: {line[:90]}")
                for ref in re.findall(r"function (offroader:[a-z0-9_/]+)", line):
                    referenced.add(ref)
    for ref in sorted(referenced):
        if ref not in funcs:
            err(f"funcție referențiată inexistentă: {ref}")
    # tag-urile minecraft
    for tagf in ("tick", "load"):
        p = os.path.join(DP, "data", "minecraft", "tags", "function", f"{tagf}.json")
        if check_json(p):
            data = json.load(open(p, encoding="utf-8"))
            for v in data.get("values", []):
                if v not in funcs:
                    err(f"tag {tagf} referențiază funcție inexistentă: {v}")
    ok(f"{len(funcs)} funcții, {len(referenced)} referințe rezolvate")


def validate_resourcepack():
    # pack.mcmeta + sounds.json
    check_json(os.path.join(RP, "pack.mcmeta"))
    snd = os.path.join(RP, "assets", "offroader", "sounds.json")
    if check_json(snd):
        data = json.load(open(snd, encoding="utf-8"))
        for event in data:
            for s in data[event]["sounds"]:
                f = os.path.join(RP, "assets", "offroader", "sounds",
                                 s["name"].split(":")[1] + ".ogg")
                if not os.path.exists(f):
                    err(f"sunet lipsă pentru «{event}»: {f}")
    # item model definitions -> modele
    items_dir = os.path.join(RP, "assets", "offroader", "items")
    models = set()
    mdir = os.path.join(RP, "assets", "offroader", "models")
    for dirpath, _, files in os.walk(mdir):
        for fn in files:
            if fn.endswith(".json"):
                rel = os.path.relpath(os.path.join(dirpath, fn), mdir)[:-5]
                models.add(f"offroader:{rel.replace(os.sep, '/')}")
    for fn in os.listdir(items_dir):
        p = os.path.join(items_dir, fn)
        if check_json(p):
            d = json.load(open(p, encoding="utf-8"))
            ref = d.get("model", {}).get("model", "")
            if ref and ref not in models:
                err(f"items/{fn} referențiază model inexistent: {ref}")
    # modele -> texturi
    for dirpath, _, files in os.walk(mdir):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            p = os.path.join(dirpath, fn)
            if not check_json(p):
                continue
            d = json.load(open(p, encoding="utf-8"))
            for key, ref in d.get("textures", {}).items():
                if key == "particle" and ref == "offroader:item/body":
                    pass
                tex = os.path.join(RP, "assets", "offroader", "textures",
                                   ref.split(":", 1)[1] + ".png")
                if not os.path.exists(tex):
                    err(f"{os.path.relpath(p, RP)}: textură inexistentă: {ref}")
    ok(f"{len(models)} modele, sunete și texturi verificate")


def validate_datapack_meta():
    check_json(os.path.join(DP, "pack.mcmeta"))
    if not os.path.exists(os.path.join(DP, "pack.png")):
        err("datapack/pack.png lipsește")
    ok("pack.mcmeta + pack.png")


# ---------------------------------------------------------------------------
def zip_pack(src_dir, zip_path, exclude_dirs=()):
    if os.path.exists(zip_path):
        os.remove(zip_path)
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, files in os.walk(src_dir):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for fn in files:
                full = os.path.join(dirpath, fn)
                arc = os.path.relpath(full, src_dir)
                z.write(full, arc)
    size = os.path.getsize(zip_path)
    print(f"  -> {os.path.relpath(zip_path, ROOT)}  ({size/1024:.1f} KB)")


if __name__ == "__main__":
    if "--regen" in sys.argv:
        if not regen():
            sys.exit(1)
    print("Validare datapack:")
    validate_datapack_meta()
    validate_mcfunctions()
    print("Validare resource pack:")
    validate_resourcepack()
    if ERRORS:
        print(f"\n{len(ERRORS)} erori — pack-urile NU au fost împachetate.")
        sys.exit(1)
    print("\nÎmpachetare:")
    zip_pack(DP, os.path.join(REL, "OffroaderDatapack.zip"))
    zip_pack(RP, os.path.join(REL, "OffroaderResourcePack.zip"))
    print("\nGata! ZIP-urile sunt în offroader/release/")
