"""
Generează toate texturile PNG pentru resource pack-ul Offroader.
Rulare: python3 gen_textures.py  (din offroader/scripts/)
Ieșire: ../resourcepack/assets/offroader/textures/item/*.png + pack.png
"""
import os
import numpy as np
from PIL import Image, ImageDraw
import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.join(HERE, "..", "resourcepack")
TEXDIR = os.path.join(RP, "assets", C.NS, "textures", "item")

rng = np.random.default_rng(20261)

# ---------------------------------------------------------------------------
# utilitare
# ---------------------------------------------------------------------------

def noise_layer(w, h, amp, seed=None):
    """Zgomot uniform -1..1 * amp."""
    r = np.random.default_rng(seed) if seed is not None else rng
    return (r.random((h, w)) * 2 - 1) * amp


def fill_region(img, rect, rgb, amp=6, seed=None):
    """Umple rect-ul (x,y,w,h) cu o culoare de bază + zgomot."""
    x, y, w, h = rect
    base = np.array(rgb, dtype=np.int16)
    n = noise_layer(w, h, amp, seed)
    px = np.clip(base[None, None, :] + n[:, :, None], 0, 255).astype(np.uint8)
    img.paste(Image.fromarray(px, "RGB"), (x, y))


def horiz_seam(img, rect, y_frac=0.5, color=(0, 0, 0), alpha=60, width=1):
    x, y, w, h = rect
    yy = y + int(h * y_frac)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([x, yy, x + w - 1, yy + width - 1], fill=(*color, alpha))
    img.alpha_composite(overlay)


def scratches(img, rect, n=14, color=(255, 255, 255, 26), seed=None):
    r = np.random.default_rng(seed) if seed is not None else rng
    x, y, w, h = rect
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for _ in range(n):
        x1 = x + int(r.integers(0, w)); y1 = y + int(r.integers(0, h))
        ln = int(r.integers(2, max(3, w // 3)))
        d.line([x1, y1, x1 + ln, y1], fill=color, width=1)
    img.alpha_composite(overlay)


def rivets(img, rect, cols=4, rows=2, color=(40, 46, 32, 255), seed=None):
    r = np.random.default_rng(seed) if seed is not None else rng
    x, y, w, h = rect
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(cols):
        for j in range(rows):
            px = x + int((i + 0.5) * w / cols) + int(r.integers(-1, 2))
            py = y + int((j + 0.5) * h / rows) + int(r.integers(-1, 2))
            d.point((px, py), fill=color)
            d.point((px, py + 1), fill=(60, 68, 50, 255))
    img.alpha_composite(overlay)


# ---------------------------------------------------------------------------
# pictori de regiuni (body.png 128x128)
# ---------------------------------------------------------------------------

def paint_body(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (107, 122, 79), amp=7, seed=11)          # olive #6b7a4f
    # degrade vertical subtil (partea de jos mai închisă)
    grad = np.linspace(0, -14, h, dtype=np.int16)[:, None, None]
    crop_box = (x, y, x + w, y + h)
    base = np.asarray(img.crop(crop_box), dtype=np.int16) + grad
    img.paste(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), (x, y))
    # linii de panou
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for yy in (int(h*0.28), int(h*0.62), int(h*0.86)):
        d.rectangle([x, y+yy, x+w-1, y+yy], fill=(58, 66, 45, 120))
    for xx in (int(w*0.22), int(w*0.5), int(w*0.78)):
        d.rectangle([x+xx, y, x+xx, y+h-1], fill=(58, 66, 45, 90))
    img.alpha_composite(overlay)
    rivets(img, rect, cols=6, rows=3, seed=21)
    scratches(img, rect, n=10, seed=31)


def paint_stripe(img, rect):
    paint_body(img, rect)
    x, y, w, h = rect
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    sw = max(2, w // 8)
    d.rectangle([x + w//2 - sw - 1, y, x + w//2 - 2, y+h-1], fill=(31, 31, 29, 255))
    d.rectangle([x + w//2 + 1, y, x + w//2 + sw, y+h-1], fill=(31, 31, 29, 255))
    img.alpha_composite(overlay)


def paint_body_dark(img, rect):
    fill_region(img, rect, (78, 89, 58), amp=5, seed=12)
    scratches(img, rect, n=6, seed=32)


def paint_fender(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (87, 100, 71), amp=6, seed=13)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([x, y, x+w-1, y], fill=(52, 60, 42, 200))
    d.rectangle([x, y+h-1, x+w-1, y+h-1], fill=(52, 60, 42, 200))
    # textură „tread" pe jumătatea de sus (suprafața aripei)
    for i in range(w):
        if i % 4 == 0:
            d.line([x+i, y+1, x+i, y+2], fill=(64, 73, 52, 160))
    img.alpha_composite(overlay)
    rivets(img, rect, cols=5, rows=2, seed=22)


def paint_grille(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (24, 24, 24), amp=3, seed=14)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(2, w - 2, 3):                     # lamele verticale cromate
        d.line([x+i, y+1, x+i, y+h-2], fill=(198, 200, 202, 255))
        d.line([x+i+1, y+1, x+i+1, y+h-2], fill=(120, 124, 128, 255))
    d.rectangle([x, y, x+w-1, y+h-1], outline=(150, 153, 156, 255))
    img.alpha_composite(overlay)


def paint_headlight(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (30, 30, 30), amp=2, seed=15)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy, r = x + w//2, y + h//2, min(w, h)//2 - 1
    for rr in range(r, 0, -1):
        t = rr / r
        if t > 0.72:   col = (35, 32, 26, 255)
        elif t > 0.5:  col = (255, 246, 204, 255)
        elif t > 0.28: col = (255, 214, 92, 255)
        else:          col = (255, 248, 170, 255)
        d.ellipse([cx-rr, cy-rr, cx+rr, cy+rr], fill=col)
    # sclipire
    d.line([cx-r//2, cy-r//3, cx-r//4, cy-r//4], fill=(255, 255, 255, 230))
    img.alpha_composite(overlay)


def paint_taillight(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (66, 12, 12), amp=3, seed=16)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([x+1, y+1, x+w-2, y+h-2], fill=(214, 44, 44, 255))
    d.rectangle([x+2, y+2, x+w-4, y+3], fill=(255, 128, 128, 255))
    img.alpha_composite(overlay)


def paint_bumper(img, rect):
    fill_region(img, rect, (36, 37, 32), amp=5, seed=17)
    scratches(img, rect, n=18, color=(70, 72, 62, 60), seed=33)
    horiz_seam(img, rect, 0.35, alpha=80)
    horiz_seam(img, rect, 0.7, alpha=80)


def paint_bullbar(img, rect):
    fill_region(img, rect, (154, 160, 166), amp=4, seed=18)
    x, y, w, h = rect
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(0, w, 4):
        d.line([x+i, y, x+i, y+h-1], fill=(110, 116, 122, 140))
    img.alpha_composite(overlay)


def paint_cage(img, rect):
    fill_region(img, rect, (46, 47, 43), amp=4, seed=19)
    scratches(img, rect, n=8, color=(90, 92, 86, 70), seed=34)


def paint_dash(img, rect):
    fill_region(img, rect, (58, 61, 64), amp=3, seed=20)
    horiz_seam(img, rect, 0.3, alpha=60)
    horiz_seam(img, rect, 0.75, alpha=60)


def paint_swheel(img, rect):
    """Volan cu colțuri TRANSPARENTE (cutout)."""
    x, y, w, h = rect
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = w // 2, h // 2
    r_out, r_in = min(w, h) // 2 - 1, min(w, h) // 3
    # inel
    d.ellipse([cx-r_out, cy-r_out, cx+r_out, cy+r_out], fill=(38, 40, 42, 255))
    d.ellipse([cx-r_in, cy-r_in, cx+r_in, cy+r_in], fill=(0, 0, 0, 0))
    # interior inel - reper negru mijlociu
    d.ellipse([cx-r_out, cy-r_out, cx+r_out, cy+r_out],
              outline=(24, 25, 26, 255))
    # butuc
    d.ellipse([cx-r_in//2, cy-r_in//2, cx+r_in//2, cy+r_in//2], fill=(26, 27, 28, 255))
    d.ellipse([cx-2, cy-2, cx+2, cy+2], fill=(120, 124, 128, 255))
    # spițe
    for dx, dy in ((-r_in, 0), (r_in, 0), (0, -r_in), (0, r_in)):
        d.line([cx, cy, cx+dx, cy+dy], fill=(38, 40, 42, 255), width=2)
    img.paste(overlay, (x, y), overlay)


def paint_seat(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (59, 50, 48), amp=4, seed=23)   # piele maro-închis
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # cusături în diamant
    for i in range(-h, w, 5):
        d.line([x+i, y+h-1, x+i+h, y], fill=(92, 74, 70, 140))
        d.line([x+i, y, x+i+h, y+h-1], fill=(92, 74, 70, 110))
    img.alpha_composite(overlay)
    scratches(img, rect, n=6, color=(120, 100, 95, 40), seed=35)


def paint_tread(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (74, 76, 70), amp=4, seed=24)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(-h, w, 4):
        d.line([x+i, y+h-1, x+i+h//2, y], fill=(51, 53, 47, 200), width=2)
        d.line([x+i+2, y+h-1, x+i+2+h//2, y], fill=(94, 96, 88, 160))
    img.alpha_composite(overlay)


def paint_frame(img, rect):
    fill_region(img, rect, (38, 39, 42), amp=4, seed=25)
    scratches(img, rect, n=8, color=(90, 90, 96, 60), seed=36)


def paint_spare(img, rect):
    """Flancă de anvelopă cu jantă (roata rezervă)."""
    x, y, w, h = rect
    fill_region(img, rect, (26, 27, 25), amp=3, seed=26)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = x + w // 2, y + h // 2
    r = min(w, h) // 2 - 1
    # jantă
    d.ellipse([cx-r//2, cy-r//2, cx+r//2, cy+r//2], fill=(143, 148, 153, 255))
    d.ellipse([cx-r//2+1, cy-r//2+1, cx+r//2-1, cy+r//2-1],
              outline=(100, 104, 108, 255))
    # spițe
    import math
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        d.line([cx, cy, cx + int(r/2 * math.cos(a)), cy + int(r/2 * math.sin(a))],
               fill=(100, 104, 108, 255), width=2)
    d.ellipse([cx-2, cy-2, cx+2, cy+2], fill=(184, 188, 192, 255))
    # profil anvelopă
    for k in range(12):
        a = k * 2 * math.pi / 12
        px, py = cx + int(r * 0.78 * math.cos(a)), cy + int(r * 0.78 * math.sin(a))
        d.point((px, py), fill=(12, 12, 12, 255))
    img.alpha_composite(overlay)


def paint_jerrycan(img, rect):
    x, y, w, h = rect
    fill_region(img, rect, (163, 51, 39), amp=5, seed=27)   # roșu
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rectangle([x+1, y+1, x+w-2, y+h-2], outline=(125, 36, 27, 255))
    # X imprimat
    d.line([x+3, y+3, x+w-4, y+h-4], fill=(110, 31, 23, 255), width=2)
    d.line([x+3, y+h-4, x+w-4, y+3], fill=(110, 31, 23, 255), width=2)
    # capac
    d.rectangle([x+w-5, y+1, x+w-2, y+4], fill=(220, 220, 218, 255))
    img.alpha_composite(overlay)


def paint_exhaust(img, rect):
    fill_region(img, rect, (63, 66, 71), amp=4, seed=28)
    x, y, w, h = rect
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(0, w, 3):
        d.line([x+i, y, x+i+2, y+h-1], fill=(30, 30, 32, 140))
    img.alpha_composite(overlay)


PAINTERS = {
    "body": paint_body, "stripe": paint_stripe, "body_dark": paint_body_dark,
    "fender": paint_fender, "grille": paint_grille, "headlight": paint_headlight,
    "taillight": paint_taillight, "bumper": paint_bumper, "bullbar": paint_bullbar,
    "cage": paint_cage, "dash": paint_dash, "swheel": paint_swheel,
    "seat": paint_seat, "tread": paint_tread, "frame": paint_frame,
    "spare": paint_spare, "jerrycan": paint_jerrycan, "exhaust": paint_exhaust,
}


def build_body():
    regions = C.layout_regions()
    img = Image.new("RGBA", (C.TEX_SIZE, C.TEX_SIZE), (0, 0, 0, 0))
    for name, rect in regions.items():
        if name not in PAINTERS:
            raise SystemExit(f"Painter lipsă pentru regiunea {name}")
        PAINTERS[name](img, rect)
    print("layout body:", regions)
    img.save(os.path.join(TEXDIR, "body.png"))


# ---------------------------------------------------------------------------
# wheel.png (32x32)
# ---------------------------------------------------------------------------

def build_wheel():
    img = Image.new("RGBA", (C.WHEEL_TEX_SIZE, C.WHEEL_TEX_SIZE), (0, 0, 0, 0))
    # flancă
    x, y, w, h = C.WHEEL_REGIONS["tire_side"]
    fill_region(img, (x, y, w, h), (24, 25, 24), amp=3, seed=41)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 1
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(20, 21, 20, 255))
    # banda de rulare pe marginile flancii
    for k in range(16):
        a = k * 2 * 3.14159 / 16
        px, py = cx + int(r * 0.9 * np.cos(a)), cy + int(r * 0.9 * np.sin(a))
        d.point((px, py), fill=(8, 8, 8, 255))
    # jantă cu 5 spițe
    d.ellipse([cx-r//2, cy-r//2, cx+r//2, cy+r//2], fill=(96, 100, 104, 255))
    d.ellipse([cx-r//2+1, cy-r//2+1, cx+r//2-1, cy+r//2-1], outline=(60, 62, 66, 255))
    import math
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        d.line([cx, cy, cx + int(r/2 * math.cos(a)), cy + int(r/2 * math.sin(a))],
               fill=(60, 62, 66, 255), width=2)
    d.ellipse([cx-2, cy-2, cx+2, cy+2], fill=(178, 182, 186, 255))
    # text SCRIS pe flancă (puncte albe)
    d.point((cx - r + 4, cy), fill=(200, 200, 195, 255))
    img.alpha_composite(overlay)
    # bandă de rulare
    tx, ty, tw, th = C.WHEEL_REGIONS["tire_tread"]
    fill_region(img, (tx, ty, tw, th), (22, 23, 22), amp=3, seed=42)
    ov2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(ov2)
    for i in range(0, tw - 2, 4):
        d2.line([tx+i, ty, tx+i+2, ty+th-1], fill=(12, 12, 12, 255), width=2)
        d2.line([tx+i+2, ty, tx+i+4, ty+th-1], fill=(44, 46, 44, 200), width=1)
    img.alpha_composite(ov2)
    img.save(os.path.join(TEXDIR, "wheel.png"))


# ---------------------------------------------------------------------------
# texturi de item (16x16) — key, steering_wheel (icon), jerrycan (icon)
# ---------------------------------------------------------------------------

def build_key_texture():
    """Metal auriu (material pentru modelul 3D al cheii)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    fill_region(img, (0, 0, 16, 16), (212, 160, 23), amp=8, seed=51)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(0, 16, 4):
        d.line([(i, 0), (i, 15)], fill=(160, 116, 14, 90))
    d.rectangle([0, 7, 15, 8], fill=(160, 116, 14, 120))
    img.alpha_composite(overlay)
    img.save(os.path.join(TEXDIR, "key.png"))


def build_wheelitem_texture():
    """Plastic întunecat (material pentru volanul 3D)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    fill_region(img, (0, 0, 16, 16), (38, 40, 42), amp=4, seed=52)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(0, 16, 5):
        d.line([(i, 0), (i, 15)], fill=(22, 23, 24, 120))
    img.alpha_composite(overlay)
    img.save(os.path.join(TEXDIR, "steering_wheel.png"))


def build_jerrycan_texture():
    """Metal roșu (material pentru bidonul 3D)."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    fill_region(img, (0, 0, 16, 16), (163, 51, 39), amp=7, seed=53)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.line([(0, 5), (15, 5)], fill=(125, 36, 27, 120))
    d.line([(0, 11), (15, 11)], fill=(125, 36, 27, 120))
    d.line([(5, 0), (5, 15)], fill=(125, 36, 27, 90))
    d.line([(11, 0), (11, 15)], fill=(125, 36, 27, 90))
    img.alpha_composite(overlay)
    img.save(os.path.join(TEXDIR, "jerrycan.png"))


# ---------------------------------------------------------------------------
# pack.png (iconiță 64x64)
# ---------------------------------------------------------------------------

def build_pack_icon():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # fundal gradient cer
    for i in range(64):
        d.line([(0, i), (63, i)], fill=(46 + i // 3, 96 + i // 4, 60 + i // 6, 255))
    # umbră
    d.ellipse([6, 50, 58, 60], fill=(20, 40, 24, 130))
    # roți
    for wx in (10, 42):
        d.ellipse([wx, 40, wx + 14, 54], fill=(20, 21, 20, 255))
        d.ellipse([wx + 4, 44, wx + 10, 50], fill=(120, 124, 128, 255))
    # caroserie olive
    d.rectangle([4, 22, 60, 46], fill=(107, 122, 79, 255), outline=(58, 66, 45, 255))
    d.rectangle([8, 26, 24, 34], fill=(150, 170, 120, 255))     # geam față
    d.rectangle([26, 14, 34, 24], fill=(46, 47, 43, 255))       # bară roll cage
    d.rectangle([36, 14, 44, 24], fill=(46, 47, 43, 255))
    d.rectangle([24, 12, 46, 16], fill=(46, 47, 43, 255))
    d.rectangle([6, 44, 16, 48], fill=(255, 214, 92, 255))      # far
    d.rectangle([48, 44, 58, 48], fill=(255, 214, 92, 255))
    d.rectangle([2, 44, 62, 48], fill=(36, 37, 32, 255))        # bumper
    d.rectangle([26, 50, 38, 54], fill=(20, 21, 20, 255))       # roată față mijloc
    img.save(os.path.join(RP, "pack.png"))
    img.save(os.path.join(HERE, "..", "datapack", "pack.png"))


if __name__ == "__main__":
    os.makedirs(TEXDIR, exist_ok=True)
    build_body()
    build_wheel()
    build_key_texture()
    build_wheelitem_texture()
    build_jerrycan_texture()
    build_pack_icon()
    print("Texturi generate în", os.path.relpath(TEXDIR, HERE))
