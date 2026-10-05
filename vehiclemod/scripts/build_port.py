#!/usr/bin/env python3
"""PORT COMPLET 1:1 — generează din zip-urile modului (din main):
  1. vehiclemod/resourcepack/  — assets/vehicle copiat din JAR (modele, texturi,
     sunete, sounds.json — namespace IDENTIC cu modul) + definiții items 1.21.4
  2. vehiclemod/plugin/src/main/resources/vehicles.json — datele tuturor
     vehiculelor (din data/vehicle/vehicles/properties/*.json din sursă)
  3. vehiclemod/release/*.zip

Rulare: python3 vehiclemod/scripts/build_port.py
"""
import json, os, shutil, zipfile, hashlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JAR = "/tmp/vmod"          # jar-ul modului dezarhivat
SRC = "/tmp/modsrc/MrCrayfishVehicleMod-1.16.X-dev"  # sursa dev
RP = os.path.join(ROOT, "vehiclemod", "resourcepack")
REL = os.path.join(ROOT, "vehiclemod", "release")
PRES = os.path.join(ROOT, "vehiclemod", "plugin", "src", "main", "resources")

# hitbox-urile din ModEntities.java (width, height) — per vehicul
HITBOX = {
    "sports_car": (1.5, 1.0), "go_kart": (1.5, 0.5), "jet_ski": (1.5, 1.0),
    "lawn_mower": (1.2, 1.0), "moped": (1.0, 1.0), "sports_plane": (3.0, 1.6875),
    "golf_cart": (2.0, 1.0), "off_roader": (2.0, 1.0), "tractor": (1.5, 1.5),
    "mini_bus": (2.0, 2.0), "dirt_bike": (1.0, 1.5), "quad_bike": (1.5, 1.0),
    "compact_helicopter": (2.0, 2.0), "vehicle_trailer": (1.5, 0.75),
    "storage_trailer": (1.0, 1.0), "fluid_trailer": (1.5, 1.5),
    "seeder": (1.5, 1.0), "fertilizer": (1.5, 1.0),
}

# vehicule terestre drivabile acum (fizica LandVehicleEntity portată);
# restul (apă/aer/remorci) urmează în faza 2
PHASE = {
    "jet_ski": "water", "sports_plane": "air", "compact_helicopter": "air",
    "sofacopter": "air", "vehicle_trailer": "trailer", "storage_trailer": "trailer",
    "fluid_trailer": "trailer", "seeder": "trailer", "fertilizer": "trailer",
}

def gen_resourcepack():
    dst = os.path.join(RP, "assets", "vehicle")
    os.makedirs(dst, exist_ok=True)
    src = os.path.join(JAR, "assets", "vehicle")
    # 1. modele + texturi + sunete + sounds.json — verbatim din mod
    for part in ("models", "textures", "sounds", "sounds.json"):
        s = os.path.join(src, part)
        d = os.path.join(dst, part)
        if os.path.isfile(s):
            shutil.copy2(s, d)
        else:
            shutil.rmtree(d, ignore_errors=True)
            shutil.copytree(s, d)
    # 2. definiții items 1.21.4 (assets/vehicle/items/<nume>.json) pentru
    #    fiecare model de item + fiecare body de vehicul
    items_dir = os.path.join(dst, "items")
    os.makedirs(items_dir, exist_ok=True)
    count = 0
    for sub in ("item", "vehicle"):
        md = os.path.join(src, "models", sub)
        if not os.path.isdir(md):
            continue
        for f in os.listdir(md):
            if not f.endswith(".json"):
                continue
            name = f[:-5]
            with open(os.path.join(items_dir, f"{name}.json"), "w") as fh:
                json.dump({"model": {"type": "minecraft:model",
                                     "model": f"vehicle:{sub}/{name}"}}, fh)
            count += 1
    # 3. pack.mcmeta (1.21.4 = format 34)
    with open(os.path.join(RP, "pack.mcmeta"), "w") as fh:
        json.dump({"pack": {"pack_format": 34, "description":
                   "MrCrayfish's Vehicle Mod — port 1:1 (server-side)"}}, fh)
    # pack.png din mod
    png = os.path.join(JAR, "vehicle_mod.png")
    if os.path.isfile(png):
        shutil.copy2(png, os.path.join(RP, "pack.png"))
    return count

def gen_vehicles_json():
    props_dir = os.path.join(SRC, "src", "generated", "resources", "data",
                             "vehicle", "vehicles", "properties")
    out = []
    for f in sorted(os.listdir(props_dir)):
        vid = f[:-5]
        d = json.load(open(os.path.join(props_dir, f)))
        pw = d.get("extended", {}).get("vehicle:powered", {})
        bt = d.get("bodyTransform") or {}
        scale = bt.get("scale", 1.0)
        tr = bt.get("translate", [0, 0, 0])
        w, h = HITBOX.get(vid, (1.5, 1.0))
        v = {
            "id": vid,
            "name": vid.replace("_", " ").title(),
            "type": PHASE.get(vid, "land"),
            "hitbox": [w, h],
            "body": {
                "model": f"vehicle:{vid}_body",
                "scale": scale,
                "translate": [tr[0] * scale / 16.0, tr[1] * scale / 16.0, tr[2] * scale / 16.0],
            },
            "wheels": [
                {"side": wh.get("side", "left"), "axle": wh.get("axle", "front"),
                 "offset": wh["offset"], "scale": wh.get("scale", [1.0, scale, scale]),
                 "model": "vehicle:standard_wheel", "render": wh.get("render", True)}
                for wh in d.get("wheels", [])
            ],
            "seats": [
                {"pos": s.get("position", [0, 4, 0]), "driver": bool(s.get("driver"))}
                for s in d.get("seats", [])
            ],
            "engine": {
                "power": pw.get("enginePower", 16.0),
                "minPitch": pw.get("minEnginePitch", 0.8),
                "maxPitch": pw.get("maxEnginePitch", 1.6),
                "sound": pw.get("engineSound", ""),
                "capacity": pw.get("energyCapacity", 20000.0),
            },
            "frontAxle": pw.get("frontAxleOffset", 14.5),
            "rearAxle": pw.get("rearAxleOffset", -14.5),
        }
        out.append(v)
    os.makedirs(PRES, exist_ok=True)
    with open(os.path.join(PRES, "vehicles.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return len(out)

def zip_rp():
    os.makedirs(REL, exist_ok=True)
    z = os.path.join(REL, "VehicleResourcePack.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(RP):
            for f in files:
                p = os.path.join(root, f)
                zf.write(p, os.path.relpath(p, RP))
    return z

if __name__ == "__main__":
    n_items = gen_resourcepack()
    n_veh = gen_vehicles_json()
    z = zip_rp()
    # URL-ul RP rămâne stabil pentru server.properties (calea veche)
    legacy = os.path.join(ROOT, "offroader", "release", "OffroaderResourcePack.zip")
    if os.path.isdir(os.path.dirname(legacy)):
        shutil.copy2(z, legacy)
    sha = hashlib.sha1(open(z, "rb").read()).hexdigest()
    print(f"RP: {n_items} iteme, zip {os.path.getsize(z)//1024}KB, sha1={sha}")
    print(f"vehicule: {n_veh} -> vehicles.json")
    open(os.path.join(REL, "rp-sha1.txt"), "w").write(sha + "\n")
    # pluginul citește sha-ul din resurse
    with open(os.path.join(PRES, "rp-sha1.txt"), "w") as fh:
        fh.write(sha + "\n")
