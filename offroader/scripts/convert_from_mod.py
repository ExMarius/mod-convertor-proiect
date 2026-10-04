"""
Convertește asset-urile offroader-ului din sursele MrCrayfish's Vehicle Mod
(sources/dev/...) în resourcepack-ul nostru vanilla (namespace offroader).

Ce face:
  1. Modele: body, wheel, key, jerrycan, steering_wheel (ținut) + swheel_car
     (volanul din mașină, cu transformarea exactă a renderer-ului coaptă în
     display.none) — remapate vehicle: -> offroader:, curățate de câmpuri
     non-vanilla (__comment, credit, texture_size, parent).
  2. Texturile vehicul:* referențiate -> assets/offroader/textures/...
  3. Sunetele: engine (jet_ski), horn, slosh (jerry_can glug).

Rulare: python3 convert_from_mod.py   (din scripts/, după ce există sources/)
"""
import json
import math
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))          # offroader/
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))    # rădăcina repo-ului
SRC = os.path.join(REPO, "sources", "dev", "MrCrayfishVehicleMod-1.16.X-dev",
                   "src", "main", "resources", "assets", "vehicle")
RP = os.path.join(ROOT, "resourcepack", "assets", "offroader")


def load(rel):
    with open(os.path.join(SRC, rel), encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("model:", os.path.relpath(path, ROOT))


def remap_textures(data):
    """vehicle:X -> offroader:X în mapa de texturi; colectează ce trebuie copiat."""
    needed = []
    tex = data.get("textures", {})
    for k, v in tex.items():
        if isinstance(v, str) and v.startswith("vehicle:"):
            tex[k] = "offroader:" + v.split(":", 1)[1]
            needed.append(tex[k])
    return needed


def strip_nonvanilla(data):
    for key in ("__comment", "credit", "texture_size", "parent"):
        data.pop(key, None)
    return data


def convert_model(src_rel, dst_rel, display_from=None):
    data = load(src_rel)
    needed = remap_textures(data)
    strip_nonvanilla(data)
    if display_from:  # ia secțiunea display din alt model
        data["display"] = load(display_from).get("display", {})
    save_json(os.path.join(RP, dst_rel), data)
    return needed


def copy_texture(ref):
    """offroader:model/x -> copiază vehicle/textures/model/x.png"""
    _, sub = ref.split(":", 1)
    src = os.path.join(SRC, "textures", sub + ".png")
    dst = os.path.join(RP, "textures", sub + ".png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    print("textură:", os.path.relpath(dst, ROOT))


def copy_sound(src_rel, name):
    src = os.path.join(SRC, src_rel)
    dst = os.path.join(RP, "sounds", name + ".ogg")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    print("sunet:", os.path.relpath(dst, ROOT))


# ---------------------------------------------------------------------------
def build_swheel_car():
    """Volanul din mașină: modelul go_kart + transformarea EXACTĂ din
    OffRoaderRenderer coaptă în display.none.

    Renderer: translate(T1); rotX(-45); translate(T2); scale(0.75); render.
    Cu centrarea −8 a modelelor, echivalentul item_display „none" este:
      display.none = {rotation:[-45,0,0], scale:0.75, translation:T}
      T = T1 + R·T2 − 0.75·R·8 + 8   (R = rotX(-45°), unități de model)
    """
    data = load("models/vehicle/go_kart_steering_wheel.json")
    remap_textures(data)
    strip_nonvanilla(data)
    # transformările pentru itemul ținut în mână (din off_road_wheel)
    wheel_disp = load("models/item/off_road_wheel.json").get("display", {})
    t1 = (-5.0, 5.6, 3.2)          # translate(-0.3125, 0.35, 0.2) blocuri ×16
    t2 = (0.0, -0.32, 0.0)         # translate(0, -0.02, 0) blocuri ×16
    a = math.radians(-45.0)
    c, s = math.cos(a), math.sin(a)
    # R = rotX(-45): (x, c·y − s·z, s·y + c·z)
    def R(v):
        return (v[0], c * v[1] - s * v[2], s * v[1] + c * v[2])
    rt2 = R(t2)
    r8 = R((8.0, 8.0, 8.0))
    T = [t1[i] + rt2[i] - 0.75 * r8[i] + 8.0 for i in range(3)]
    data["display"] = dict(wheel_disp)
    data["display"]["none"] = {
        "rotation": [-45.0, 0.0, 0.0],
        "translation": [round(v, 4) for v in T],
        "scale": [0.75, 0.75, 0.75],
    }
    save_json(os.path.join(RP, "models", "item", "swheel_car.json"), data)
    print(f"  display.none translation = {[round(v, 3) for v in T]}")


def main():
    if not os.path.isdir(SRC):
        raise SystemExit(f"Sursele modului lipsesc: {SRC}\n"
                         "Rulează setup: vezi README (sources/dev trebuie extras).")
    needed = []
    # caroseria — geometria EXACTĂ din mod (120+ cuburi)
    needed += convert_model("models/vehicle/off_roader_body.json",
                            "models/item/body.json")
    # roata off-road (model de item din Blockbench)
    needed += convert_model("models/item/off_road_wheel.json",
                            "models/item/wheel.json")
    # volanul ținut în mână + cel din mașină
    needed += convert_model("models/vehicle/go_kart_steering_wheel.json",
                            "models/item/steering_wheel.json",
                            display_from="models/item/off_road_wheel.json")
    build_swheel_car()
    # cheia + bidonul
    needed += convert_model("models/item/key.json", "models/item/key.json")
    needed += convert_model("models/item/jerry_can.json",
                            "models/item/jerrycan.json")

    for ref in sorted(set(needed)):
        copy_texture(ref)

    # sunetele de la offroader: motor de jet_ski, claxonul vehiculului, glug
    copy_sound("sounds/entity/jet_ski/engine.ogg", "engine")
    copy_sound("sounds/entity/vehicle/horn.ogg", "horn")
    copy_sound("sounds/item/jerry_can/liquid_glug.ogg", "slosh")
    print("Conversie completă.")


if __name__ == "__main__":
    main()
