"""
Randează o previzualizare izometrică a offroader-ului (body + 4 roți) direct
din modelele JSON + texturile PNG generate. Ieșire: ../preview.png
"""
import json
import math
import os
import numpy as np
from PIL import Image, ImageDraw
import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.join(HERE, "..", "resourcepack", "assets", C.NS)
OUT = os.path.join(HERE, "..", "preview.png")

PPU = C.PX_PER_UNIT


def load_tex(name):
    return np.asarray(Image.open(os.path.join(RP, "textures", "item", name + ".png")).convert("RGBA"))


def uv_color(tex, uv, size):
    u1, v1, u2, v2 = uv
    u1, v1 = max(0, u1), max(0, v1)
    u2, v2 = min(tex.shape[1], u2), min(tex.shape[0], v2)
    if u2 <= u1 or v2 <= v1:
        return (255, 0, 255)
    block = tex[v1:v2, u1:u2]
    a = block[..., 3].astype(float) / 255
    if a.mean() < 0.3:                       # zonă transparentă -> albastru „missing"
        return (120, 120, 160)
    rgb = (block[..., :3].astype(float) * a[..., None]).sum(axis=(0, 1)) / (a.sum() + 1e-6)
    return tuple(int(c) for c in rgb)


def rot_matrix(axis, deg, origin):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        R = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    elif axis == "z":
        R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    else:
        R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    o = np.array(origin, dtype=float)

    def f(p):
        return (R @ (np.array(p, dtype=float) - o)) + o
    return f


FACE_CORNERS = {
    "north": [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)],
    "south": [(1, 1, 1), (0, 1, 1), (0, 0, 1), (1, 0, 1)],
    "east":  [(1, 1, 1), (1, 1, 0), (1, 0, 0), (1, 0, 1)],
    "west":  [(0, 1, 0), (0, 1, 1), (0, 0, 1), (0, 0, 0)],
    "up":    [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
    "down":  [(0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1)],
}
NORMALS = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0),
           "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
SHADE = {"up": 1.0, "down": 0.45, "north": 0.8, "south": 0.62,
         "east": 0.7, "west": 0.88}
AXES = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}


def element_faces(el, tex, offset=(0, 0, 0), scale=1.0):
    a, b = el["from"], el["to"]
    rot = el.get("rotation")
    xf = None
    if rot:
        xf = rot_matrix(rot["axis"], rot["angle"], rot["origin"])
    ox, oy, oz = offset
    faces = []
    for fname, corners in FACE_CORNERS.items():
        fd = el["faces"].get(fname)
        if fd is None:
            continue
        pts = []
        for cx, cy, cz in corners:
            p = [a[0] + cx * (b[0] - a[0]), a[1] + cy * (b[1] - a[1]),
                 a[2] + cz * (b[2] - a[2])]
            if xf:
                p = list(xf(p))
            pts.append(((p[0] - 8) * scale + 8 + ox,
                        (p[1] - 8) * scale + 8 + oy,
                        (p[2] - 8) * scale + 8 + oz))
        base = fd["texture"].lstrip("#")
        color = uv_color(tex, [int(u) for u in fd["uv"]], None)
        faces.append((pts, fname, color))
    return faces


def main():
    body = json.load(open(os.path.join(RP, "models", "item", "body.json")))
    wheel = json.load(open(os.path.join(RP, "models", "item", "wheel.json")))
    tex_body = load_tex("body")
    tex_wheel = load_tex("wheel")

    faces = []
    for el in body["elements"]:
        faces += element_faces(el, tex_body)

    # pozițiile roților în spațiul modelului (din config: local (x_st,y,z_față))
    # model_x = 8 - local_x/0.09375 ; model_z = 8 - local_z/0.09375
    u = 1.0 / 0.09375
    for tag, kind, model, pos, extra in C.FOLLOWERS:
        if kind != "item_display" or "offroader:wheel" not in (model or ""):
            continue
        lx, ly, lz = pos
        mx = 8 - lx * u
        my = 8 + (ly - 0.75) * u
        mz = 8 - lz * u
        for el in wheel["elements"]:
            faces += element_faces(el, tex_wheel,
                                   offset=(mx - 8, my - 8, mz - 8))

    # --- proiecție izometrică ---
    W, H = 1100, 720
    img = Image.new("RGB", (W, H), (168, 196, 174))
    d = ImageDraw.Draw(img)
    # sol
    d.ellipse([W//2 - 330, H - 92, W//2 + 330, H - 22], fill=(120, 148, 108))

    ax, ay = math.radians(30), math.radians(30)

    def proj(p):
        x, y, z = p
        # rotim scena: privire din față-stânga-sus
        X = (x - z) * math.cos(ax)
        Y = (x + z) * math.sin(ay) - y
        s = 9.5
        return (W / 2 + X * s, H - 120 + Y * s)

    def depth(p):
        x, y, z = p
        return x * 0.5 + z * 0.86 + y * 0.001

    drawn = []
    for pts, fname, color in faces:
        c = tuple(int(v * SHADE[fname]) for v in color[:3])
        poly = [proj(p) for p in pts]
        dp = sum(depth(p) for p in pts) / 4
        drawn.append((dp, poly, c))
    drawn.sort(key=lambda t: t[0])
    for dp, poly, c in drawn:
        if len(poly) >= 3:
            d.polygon(poly, fill=c, outline=tuple(int(v * 0.75) for v in c))

    img.save(OUT)
    print("previzualizare:", os.path.relpath(OUT, HERE),
          f"({len(drawn)} fețe)")


if __name__ == "__main__":
    main()
