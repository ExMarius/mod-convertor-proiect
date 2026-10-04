"""
Generează modelele JSON pentru resource pack:
  - body.json  : caroseria offroader-ului (~47 elemente, front = -Z)
  - wheel.json : roata (octogon din 4 boxe rotite, axa pe X)
  - key.json, steering_wheel.json, jerrycan.json : modele 3D de item

UV-urile fețelor sunt alocate automat în regiunile din config.REGIONS.
Rulare: python3 gen_model.py
"""
import json
import os
from collections import defaultdict
import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "resourcepack", "assets", C.NS, "models", "item")
ITEMS = os.path.join(HERE, "..", "resourcepack", "assets", C.NS, "items")

# ---------------------------------------------------------------------------
# alocare UV în regiuni (shelf packing)
# ---------------------------------------------------------------------------

# Materiale fără orientare (noise/uniform): fețele pot partaja UV și pot fi
# rotite la 90° în alocare ca să încapă eficient.
SHARED_MATERIALS = {"frame", "cage", "bumper", "bullbar", "body_dark",
                    "tread", "seat", "exhaust", "dash", "body",
                    "fender", "tire_tread", "tire_side", "item"}
# Materiale orientate (dungi, lamele, sprite-uri) — UV unic, fără rotire.
ORIENTED_MATERIALS = {"stripe", "grille", "headlight", "taillight",
                      "swheel", "spare", "jerrycan", "item", "fender_x"}


class UVAllocator:
    def __init__(self, regions, px_per_unit=1):
        self.regions = {name: dict(x=x, y=y, w=w, h=h,
                                   cx=x, cy=y, rh=0)
                        for name, (x, y, w, h) in regions.items()}
        self.ppu = px_per_unit
        self.cache = {}

    def alloc(self, region, w, h, shared=False):
        w = max(1, int(w * self.ppu + 0.999))
        h = max(1, int(h * self.ppu + 0.999))
        swapped = False
        if shared and h > w:          # rotește fețele lungi
            w, h = h, w
            swapped = True
        key = (region, w, h) if shared else None
        if key is not None and key in self.cache:
            return self.cache[key], True
        r = self.regions[region]
        if r["cx"] + w > r["x"] + r["w"]:
            r["cy"] += r["rh"]
            r["cx"] = r["x"]
            r["rh"] = 0
        if r["cy"] + h > r["y"] + r["h"]:
            raise SystemExit(
                f"Regiunea '{region}' s-a umplut (ceream {w}x{h} la y={r['cy']}). "
                f"Mărește regiunea în config.py.")
        u1, v1 = r["cx"], r["cy"]
        r["cx"] += w
        r["rh"] = max(r["rh"], h)
        rect = [u1, v1, u1 + w, v1 + h]
        if key is not None:
            self.cache[key] = rect
        return rect, swapped


def face_size(f, a, b):
    """Dimensiunea (w,h) în pixeli pentru fața f a boxei from=a to=b."""
    dx, dy, dz = (b[0] - a[0]), (b[1] - a[1]), (b[2] - a[2])
    if f in ("north", "south"):
        return abs(dx), abs(dy)
    if f in ("east", "west"):
        return abs(dz), abs(dy)
    return abs(dx), abs(dz)          # up / down


class ModelBuilder:
    def __init__(self, allocator, texture_file):
        self.alloc = allocator
        self.texture_file = texture_file   # ex: "offroader:item/body"
        self.elements = []
        self.materials = set()

    def box(self, name, a, b, mat, faces=None, rotation=None, no_cull=True):
        """a, b = colțuri (from/to); faces = dict față->material (default mat)."""
        if rotation is None:
            rotation = {}
        for i in range(3):
            if not (-16.001 <= min(a[i], b[i]) and max(a[i], b[i]) <= 32.001):
                raise SystemExit(f"{name}: coordonate în afara limitelor [-16,32]: {a} {b}")
        face_mats = {f: (faces or {}).get(f, mat) for f in
                     ("down", "up", "north", "south", "east", "west")}
        el = {
            "name": name,
            "from": list(a), "to": list(b),
            "faces": {},
        }
        if rotation:
            el["rotation"] = rotation
        for f, m in face_mats.items():
            w, h = face_size(f, a, b)
            shared = m in SHARED_MATERIALS
            uv, _sw = self.alloc.alloc(m, w, h, shared=shared)
            el["faces"][f] = {"uv": uv, "texture": f"#{m}"}
            self.materials.add(m)
        self.elements.append(el)

    def build(self):
        textures = {m: f"{C.NS}:item/{self.texture_file}" for m in sorted(self.materials)}
        textures["particle"] = f"{C.NS}:item/{self.texture_file}"
        return {"credit": "Offroader vanilla datapack project",
                "textures": textures,
                "elements": self.elements}


# ---------------------------------------------------------------------------
# BODY — offroader (front = -Z, sol = y0, centrat pe x=8)
# ---------------------------------------------------------------------------

def build_body(alloc):
    m = ModelBuilder(alloc, "body")
    B = m.box

    # --- șasiu & podea ---
    B("frame_l_a", (-0.7, 1, -13), (0.5, 5, 8), "frame")
    B("frame_l_b", (-0.7, 1, 8), (0.5, 5, 29), "frame")
    B("frame_r_a", (15.2, 1, -13), (16.3, 5, 8), "frame")
    B("frame_r_b", (15.2, 1, 8), (16.3, 5, 29), "frame")
    B("floor_a", (-0.7, 5, -4), (16.3, 5.5, 12.5), "tread",
      faces={"up": "tread", "down": "tread"})
    B("floor_b", (-0.7, 5, 12.5), (16.3, 5.5, 29), "tread",
      faces={"up": "tread", "down": "tread"})

    # --- față ---
    B("nose", (-1, 8, -14), (17, 11, -11), "body",
      faces={"north": "grille", "up": "body"})
    B("hood", (-1, 10, -11), (17, 11, 0), "body", faces={"up": "stripe"})
    B("headlight_l", (0, 9, -14.6), (5, 11, -13.5), "headlight")
    B("headlight_r", (11, 9, -14.6), (16, 11, -13.5), "headlight")
    B("bumper_f", (-2, 4, -15.5), (18, 7.5, -14), "bumper")
    B("bullbar_h", (-1, 9, -16), (17, 10, -15), "bullbar")
    B("bullbar_v1", (2, 7, -16), (3, 10, -15), "bullbar")
    B("bullbar_v2", (13, 7, -16), (14, 10, -15), "bullbar")

    # --- laterale / aripi ---
    B("fender_fl", (-4.5, 9.5, -11), (0.5, 12, -1), "fender")
    B("fender_fr", (15.5, 9.5, -11), (20.5, 12, -1), "fender")
    B("fender_rl", (-4.5, 9.5, 17), (0.5, 12, 27.5), "fender")
    B("fender_rr", (15.5, 9.5, 17), (20.5, 12, 27.5), "fender")
    B("sill_l", (-1, 5, -1), (0, 8, 16.5), "body_dark")
    B("sill_r", (16, 5, -1), (17, 8, 16.5), "body_dark")
    B("uppersill_l", (-1, 8, -0.5), (0, 10, 16), "body")
    B("uppersill_r", (16, 8, -0.5), (17, 10, 16), "body")
    B("well_fl", (-1, 5, -11), (-0.85, 9.5, -1), "body_dark")
    B("well_fr", (16.85, 5, -11), (17, 9.5, -1), "body_dark")
    B("well_rl", (-1, 5, 17), (-0.85, 9.5, 27.5), "body_dark")
    B("well_rr", (16.85, 5, 17), (17, 9.5, 27.5), "body_dark")

    # --- bord + volan ---
    B("dash", (-1, 10, 0.5), (17, 12, 3), "dash")
    B("steering_disc", (6.0, 12, 2.5), (9.0, 14.5, 3.2), "swheel",
      rotation={"origin": [7.5, 13.0, 2.85], "axis": "x", "angle": -25})

    # --- scaune ---
    B("console", (9.5, 5, 6), (10.5, 9.9, 10), "bumper")
    B("driver_cushion", (5, 9.9, 6), (9.5, 11, 10), "seat")
    B("driver_back", (5, 11, 9.5), (9.5, 16.5, 11), "seat")
    B("pass_cushion", (11, 9.9, 5), (15.5, 11, 9), "seat")
    B("pass_back", (11, 11, 9), (15.5, 16.5, 10.5), "seat")
    B("bench_cushion", (1, 9.9, 16), (16, 11, 20.4), "seat")
    B("bench_back", (1, 11, 20.4), (16, 16.5, 22), "seat")

    # --- roll cage + parbriz ---
    B("ws_pillar_l", (-1, 11, 0.5), (0, 24, 1.5), "cage")
    B("ws_pillar_r", (16, 11, 0.5), (17, 24, 1.5), "cage")
    B("ws_midbar", (-1, 16.5, 0.5), (17, 17.5, 1.5), "cage")
    B("cage_post_l", (-1, 10, 20), (0, 24, 21), "cage")
    B("cage_post_r", (16, 10, 20), (17, 24, 21), "cage")
    B("top_rail_l", (-1, 23, 0.5), (0, 24, 21), "cage")
    B("top_rail_r", (16, 23, 0.5), (17, 24, 21), "cage")
    B("top_cross_f", (-1, 23, 0.5), (17, 24, 1.5), "cage")
    B("top_cross_r", (-1, 23, 20), (17, 24, 21), "cage")
    B("lightbar", (2, 24, 0.5), (14, 25, 2), "bumper", faces={"north": "headlight"})

    # --- spate ---
    B("rear_panel", (-0.5, 7, 29), (17, 11, 30), "body")
    B("bumper_r", (-1, 4, 29.5), (18, 7, 31), "bumper")
    B("taillight_l", (0, 8, 29.5), (3, 10, 30.5), "taillight")
    B("taillight_r", (14, 8, 29.5), (17, 10, 30.5), "taillight")
    B("spare", (5, 9, 30), (11, 15, 31.5), "body_dark",
      faces={"south": "spare"})
    B("jerry_mount", (11.5, 10, 30), (14.5, 13.5, 31.5), "jerrycan")
    B("exhaust", (15, 2.5, 29), (16, 3.5, 31), "exhaust")

    return m.build()


# ---------------------------------------------------------------------------
# WHEEL — octogon din 4 boxe, axa pe X (se învârte în jurul lui X)
# ---------------------------------------------------------------------------

def build_wheel(alloc):
    m = ModelBuilder(alloc, "wheel")
    B = m.box
    # boxe „verticale" și „orizontale" (secțiunea în planul Y-Z)
    B("tire_v", (6.25, 5.2, 3.3), (9.75, 10.8, 12.7), "tire_tread",
      faces={"east": "tire_side", "west": "tire_side"})
    B("tire_h", (6.25, 3.3, 5.2), (9.75, 12.7, 10.8), "tire_tread",
      faces={"east": "tire_side", "west": "tire_side"})
    B("tire_d1", (6.25, 5.2, 3.3), (9.75, 10.8, 12.7), "tire_tread",
      faces={"east": "tire_side", "west": "tire_side"},
      rotation={"origin": [8.0, 8.0, 8.0], "axis": "x", "angle": 45})
    B("tire_d2", (6.25, 5.2, 3.3), (9.75, 10.8, 12.7), "tire_tread",
      faces={"east": "tire_side", "west": "tire_side"},
      rotation={"origin": [8.0, 8.0, 8.0], "axis": "x", "angle": -45})
    return m.build()


# ---------------------------------------------------------------------------
# ITEME 3D — cheie, volan, bidon
# ---------------------------------------------------------------------------

DISPLAY_KEY = {
    "key": {
        "gui": {"rotation": [30, 225, 0], "scale": 0.8},
        "ground": {"translation": [0, 2, 0], "scale": 0.4},
        "fixed": {"rotation": [0, 90, 0], "scale": 0.7},
        "thirdperson_righthand": {"rotation": [0, 90, 55], "translation": [0, 2, 1], "scale": 0.9},
        "thirdperson_lefthand": {"rotation": [0, 90, 55], "translation": [0, 2, 1], "scale": 0.9},
        "firstperson_righthand": {"rotation": [0, -135, 25], "translation": [1, 1, 1], "scale": 0.8},
        "firstperson_lefthand": {"rotation": [0, -135, 25], "translation": [1, 1, 1], "scale": 0.8},
    },
    "steering_wheel": {
        "gui": {"rotation": [0, 315, 0], "scale": 1.0},
        "ground": {"translation": [0, 2, 0], "scale": 0.4},
        "fixed": {"scale": 0.7},
        "thirdperson_righthand": {"rotation": [0, 90, -35], "translation": [1, 1, 2], "scale": 0.9},
        "thirdperson_lefthand": {"rotation": [0, 90, -35], "translation": [1, 1, 2], "scale": 0.9},
        "firstperson_righthand": {"rotation": [0, 155, 0], "translation": [0, 1, 0], "scale": 0.8},
        "firstperson_lefthand": {"rotation": [0, 155, 0], "translation": [0, 1, 0], "scale": 0.8},
    },
    "jerrycan": {
        "gui": {"rotation": [30, 225, 0], "scale": 0.9},
        "ground": {"translation": [0, 2, 0], "scale": 0.4},
        "fixed": {"rotation": [0, 90, 0], "scale": 0.7},
        "thirdperson_righthand": {"rotation": [45, 90, 0], "translation": [0, 1.5, 1], "scale": 0.85},
        "thirdperson_lefthand": {"rotation": [45, 90, 0], "translation": [0, 1.5, 1], "scale": 0.85},
        "firstperson_righthand": {"rotation": [0, 135, 0], "translation": [1, 1, 0], "scale": 0.85},
        "firstperson_lefthand": {"rotation": [0, 135, 0], "translation": [1, 1, 0], "scale": 0.85},
    },
}

# „regiuni" mici pentru texturile de item (fiecare 16x16, un singur material)
ITEM_REGIONS = {"item": (0, 0, 16, 16)}


def build_items():
    out = {}
    # --- cheie ---
    a = UVAllocator(ITEM_REGIONS)
    m = ModelBuilder(a, "key")
    m.box("bow", (4, 4, 7), (12, 12, 9), "item")
    m.box("blade", (7, 7, 4), (9, 9, 7), "item")
    m.box("teeth", (7, 7, 3), (8, 9, 4), "item")
    j = m.build(); j["display"] = DISPLAY_KEY["key"]
    out["key"] = j

    # --- volan (inel octogonal pe axa Z) ---
    a = UVAllocator(ITEM_REGIONS)
    m = ModelBuilder(a, "steering_wheel")
    m.box("ring_h", (3, 7, 7.4), (13, 9, 8.6), "item")
    m.box("ring_v", (6.5, 3, 7.4), (9.5, 13, 8.6), "item")
    m.box("ring_d1", (3, 7, 7.4), (13, 9, 8.6), "item",
          rotation={"origin": [8.0, 8.0, 8.0], "axis": "z", "angle": 45})
    m.box("ring_d2", (3, 7, 7.4), (13, 9, 8.6), "item",
          rotation={"origin": [8.0, 8.0, 8.0], "axis": "z", "angle": -45})
    m.box("hub", (7, 7, 7.2), (9, 9, 8.8), "item")
    j = m.build(); j["display"] = DISPLAY_KEY["steering_wheel"]
    out["steering_wheel"] = j

    # --- bidon ---
    a = UVAllocator(ITEM_REGIONS)
    m = ModelBuilder(a, "jerrycan")
    m.box("can", (4, 3, 6.5), (12, 11, 9.5), "item")
    m.box("handle", (4.5, 11, 6.5), (11.5, 12, 9.5), "item")
    m.box("spout", (9, 9, 5.5), (11, 11, 6.5), "item")
    j = m.build(); j["display"] = DISPLAY_KEY["jerrycan"]
    out["jerrycan"] = j
    return out


# ---------------------------------------------------------------------------
# item model definitions (assets/<ns>/items/*.json) — referite de componenta
# minecraft:item_model din datapack / give.
# ---------------------------------------------------------------------------

ITEM_DEFS = {
    "body": "offroader:item/body",
    "wheel": "offroader:item/wheel",
    "key": "offroader:item/key",
    "steering_wheel": "offroader:item/steering_wheel",
    "jerrycan": "offroader:item/jerrycan",
}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)
    print("scris:", os.path.relpath(path, HERE))


if __name__ == "__main__":
    regions = C.layout_regions()
    alloc_body = UVAllocator(regions, C.PX_PER_UNIT)
    body = build_body(alloc_body)
    write_json(os.path.join(MODELS, "body.json"), body)

    alloc_wheel = UVAllocator(C.WHEEL_REGIONS, C.WHEEL_PX_PER_UNIT)
    wheel = build_wheel(alloc_wheel)
    write_json(os.path.join(MODELS, "wheel.json"), wheel)

    for name, model in build_items().items():
        write_json(os.path.join(MODELS, f"{name}.json"), model)

    for name, model_ref in ITEM_DEFS.items():
        write_json(os.path.join(ITEMS, f"{name}.json"),
                   {"model": {"type": "minecraft:model", "model": model_ref}})

    print(f"\nbody: {len(body['elements'])} elemente, "
          f"materiale: {sorted(body['textures'].keys())}")
    print(f"wheel: {len(wheel['elements'])} elemente")
