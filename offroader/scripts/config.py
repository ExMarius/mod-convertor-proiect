"""
Configurație comună pentru generatorul Offroader (partea de resource pack).

Convenții:
- Spațiul modelului: 16 unități = 1 bloc; modelul e centrat pe (8,8,8) = poziția entității.
- Display entity-ul caroseriei e plasat la ^0 ^0.75 ^0 relativ la cal, cu scale 1.5:
      punctul de model (mx,my,mz) -> world = ent + (m-8)*0.09375
  => model y=0  == nivelul solului (roțile ating pământul la y=0).
- FAȚETA modelului: -Z (nord în spațiul modelului). Calul "înainte" = ^ ^ ^1 (local +Z).
  Rotația display-ului mapează -Z al modelului pe direcția de mers.
- Dacă mașina merge cu spatele în joc: /scoreboard players set #flip offr.dummy 1
  (adăugat live, fără regenerare). Dacă rotile se învârt invers: #spinflip offr.dummy 1.
"""

NS = "offroader"

# Scale-ul display-urilor (caroserie + roți): modelul (16 unități = 1 bloc)
# e randat la 1.5x => mașina are ~4.4 blocuri lungime.
DISPLAY_SCALE = 1.5

# Dimensiuni atlas: body.png 256x256 (2 px / unitate de model), wheel.png 64x64 (1 px / unitate)
TEX_SIZE = 256
WHEEL_TEX_SIZE = 64
PX_PER_UNIT = 2      # pentru caroserie
WHEEL_PX_PER_UNIT = 1  # pentru roți (aspect „chunky")

# ---------------------------------------------------------------------------
# MĂRIMI de regiuni de textură pe body.png — pozițiile sunt calculate automat
# (shelf-packing determinist) de layout_regions(); gen_textures.py pictează
# regiunile, gen_model.py decupează UV-uri în ele.
# ---------------------------------------------------------------------------
REGION_SIZES = {
    "body":      (96, 88),   # olive panels + zgomot + nituri
    "stripe":    (48, 32),   # olive cu 2 dungi negre de-a lungul lui v
    "body_dark": (44, 40),   # olive închis (etanșări, pasaje)
    "fender":    (56, 56),   # aripi olive închis
    "grille":    (60, 16),   # grilă neagră cu lamele crom
    "exhaust":   (24, 16),   # metal întunecat + funingine
    "bumper":    (88, 48),   # negru mat + zgârieturi
    "headlight": (24, 24),   # far radial galben
    "taillight": (16, 16),   # stop roșu
    "bullbar":   (72, 24),   # argintiat periat
    "cage":      (64, 40),   # oțel cărbunos (roll cage)
    "dash":      (48, 24),   # gri bord
    "swheel":    (40, 40),   # volan transparent (RGBA, colțuri goale)
    "seat":      (48, 56),   # piele neagră cu cusături
    "tread":     (72, 84),   # podea placă antiderapantă
    "frame":     (48, 28),   # șasiu gri închis
    "spare":     (48, 48),   # anvelopă + jantă (rota rezervă)
    "jerrycan":  (32, 32),   # bidon roșu
}


def layout_regions(sizes=None, width=TEX_SIZE, height=TEX_SIZE):
    """Așază dreptunghiurile pe rânduri (shelf), determinist, sortate după înălțime."""
    sizes = sizes or REGION_SIZES
    items = sorted(sizes.items(), key=lambda kv: (-kv[1][1], -kv[1][0], kv[0]))
    pos, x, y, rh = {}, 0, 0, 0
    for name, (w, h) in items:
        if w > width:
            raise SystemExit(f"Regiunea {name} ({w} px) nu încape pe un rând de {width} px")
        if x + w > width:            # rând nou
            x, rh = 0, 0
            y = max(p[1] + p[3] for p in pos.values()) if pos else 0
        if y + h > height:
            raise SystemExit(f"Atlas plin la regiunea {name} (y={y}, h={h})")
        pos[name] = (x, y, w, h)
        x += w
        rh = max(rh, h)
    # verificare suprapuneri
    rects = list(pos.values())
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and \
               a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                raise SystemExit(f"Regiuni suprapuse (bug packer): {a} vs {b}")
    return pos


# Regiuni pe wheel.png (64x64)
WHEEL_REGIONS = {
    "tire_side":  (0, 0, 44, 44),   # flankă anvelopă + jantă cu spițe
    "tire_tread": (44, 0, 20, 64),  # bandă de rulare
}

# ---------------------------------------------------------------------------
# MATERIALE = ce regiune folosește fiecare element al modelului.
# ---------------------------------------------------------------------------
MATERIAL_REGION = {
    "body", "stripe", "body_dark", "fender", "grille", "headlight", "taillight",
    "bumper", "bullbar", "cage", "dash", "swheel", "seat", "tread", "frame",
    "spare", "jerrycan", "exhaust",
}

# ---------------------------------------------------------------------------
# Urmăritorii vehiculului: entități teleportate în fiecare tick relativ la cal.
#   pos = (x_stânga, y_sus, z_față) în blocuri, în cadru local al calului (^ ^ ^).
#   x pozitiv = stânga calului; z pozitiv = înainte.
# Aceeași tabelă generează summon-urile și funcțiile fl_* (gen_layout.py).
# ---------------------------------------------------------------------------
FOLLOWERS = [
    # tag,             tip,           model/extra,      pos(x,y,z),            extra
    ("offr_body", "item_display", "offroader:body", (0.0, 0.75, 0.0),   {"yaw": True}),
    ("offr_w0",   "item_display", "offroader:wheel", (-0.99, 0.44, 1.32), {"yaw": True, "spin": True}),  # față-stânga
    ("offr_w1",   "item_display", "offroader:wheel", (0.99, 0.44, 1.32),  {"yaw": True, "spin": True}),  # față-stânga
    ("offr_w2",   "item_display", "offroader:wheel", (-0.99, 0.44, -1.35), {"yaw": True, "spin": True}), # spate-dreapta
    ("offr_w3",   "item_display", "offroader:wheel", (0.99, 0.44, -1.35),  {"yaw": True, "spin": True}), # spate-stânga
    ("offr_name", "text_display", "Offroader",      (0.0, 2.75, 0.0),    {}),
    ("offr_s1",   "armor_stand",  None,             (-0.52, 1.02, 0.1),  {"seat": True}),   # față-dreapta
    ("offr_s2",   "armor_stand",  None,             (0.5, 1.02, -0.95),  {"seat": True}),   # spate-stânga
    ("offr_s3",   "armor_stand",  None,             (-0.5, 1.02, -0.95), {"seat": True}),   # spate-dreapta
    ("offr_i0",   "interaction",  "driver",         (0.0, 0.25, 0.2),    {"w": 1.3, "h": 1.5}),
    ("offr_i1",   "interaction",  "seat",           (-0.52, 0.25, 0.1),  {"w": 0.9, "h": 1.3}),
    ("offr_i2",   "interaction",  "seat",           (0.5, 0.25, -0.95),  {"w": 0.9, "h": 1.3}),
    ("offr_i3",   "interaction",  "seat",           (-0.5, 0.25, -0.95), {"w": 0.9, "h": 1.3}),
]

# Aliniere scaun-model: butul șoferului (cale) e la ~(0, 1.05, 0) local.
# Pernele de scaun din model sunt puse la y_model = 9.9..11  (11 -> 1.03 bloc).
