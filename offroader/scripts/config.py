"""
Configurația offroader-ului — sursa unică de adevăr pentru generatoare.

Geometria și constantele sunt luate 1:1 din MrCrayfish's Vehicle Mod
(VehiclePropertiesGen.java, offroader):
  - bodyTransform scale 1.4
  - roți: offset (±10, 0, ±14.5), scară 1.4
  - scaune: (5,4,−3) șofer, (−5,4,−3), (5,11.5,−14.5), (−5,3.5,−18.9)
  - motor LARGE_MOTOR, pitch 0.8..1.6, sunet = jet_ski engine
  - unghi maxim virare 35°

Convenții:
  - coordonatele din mod: unități de model (16 = 1 bloc la scară 1),
    +x = DREAPTA vehiculului, +y = sus, +z = FAȚĂ.
  - coordonatele Minecraft locale (execute ^): ^x = stânga, ^y = sus, ^z = față.
"""

NS = "offroader"

# scara vehiculului (mod: Transform.create(1.4))
DISPLAY_SCALE = 1.4
# 1 unitate de model, la scara vehiculului, în blocuri
U = DISPLAY_SCALE / 16.0
# originea vehiculului deasupra solului = raza roții
# (roata: 4..12 pe y → raza 4 unități × 1.4 / 16)
VEHICLE_ORIGIN_Y = 4 * U   # 0.35 blocuri

# cât mai jos e așezat armor stand-ul de scaun față de poziția din mod
# (compensează offsetul de „călărie" al jucătorului; se reglează în joc)
SEAT_RIDER_DROP = 0.35


def mod_to_mc(x, y, z):
    """(x,y,z) din mod -> (^x,^y,^z) Minecraft, relativ la CAL (sol).

    Offseturile din mod sunt relative la ORIGINEA vehiculului (0.35 blocuri
    deasupra solului), deci adăugăm VEHICLE_ORIGIN_Y.
    """
    return (-x * U, VEHICLE_ORIGIN_Y + y * U, z * U)


# ---------------------------------------------------------------------------
# Urmăritorii: (tag, tip, model, poziție ^ față de CAL, extra)
#   tip: item_display | text_display | armor_stand | interaction
#   extra: yaw/spin/steer pentru display-uri; w/h pentru interaction-uri
# ---------------------------------------------------------------------------
def _seat(tag, seat_xyz):
    x, y, z = mod_to_mc(*seat_xyz)
    return (tag, "armor_stand", None,
            (x, y - SEAT_RIDER_DROP, z), {})


def _inter(tag, seat_xyz, role, w=0.9, h=1.3):
    x, y, z = mod_to_mc(*seat_xyz)
    return (tag, "interaction", None,
            (x, y, z), {"role": role, "w": w, "h": h})


FOLLOWERS = [
    # caroseria — geometria EXACTĂ din mod (163 cuburi), centrată pe origine
    ("offr_body", "item_display", "offroader:body",
     mod_to_mc(0, 0, 0), {"yaw": True}),
    # volanul din mașină (modelul go_kart, transformarea renderer-ului
    # este coaptă în display.none al modelului swheel_car)
    ("offr_swheel", "item_display", "offroader:swheel_car",
     mod_to_mc(0, 0, 0), {"yaw": True}),
    # roțile — față (cu direcție), spate
    ("offr_w0", "item_display", "offroader:wheel",   # față-stânga
     mod_to_mc(-10, 0, 14.5), {"yaw": True, "spin": True, "steer": True}),
    ("offr_w1", "item_display", "offroader:wheel",   # față-dreapta
     mod_to_mc(10, 0, 14.5), {"yaw": True, "spin": True, "steer": True}),
    ("offr_w2", "item_display", "offroader:wheel",   # spate-stânga
     mod_to_mc(-10, 0, -14.5), {"yaw": True, "spin": True}),
    ("offr_w3", "item_display", "offroader:wheel",   # spate-dreapta
     mod_to_mc(10, 0, -14.5), {"yaw": True, "spin": True}),
    # numele deasupra mașinii
    ("offr_name", "text_display", None, (0.0, 2.15, 0.0), {}),
    # scaunele pasagerilor (șoferul stă pe cal, ca să poată conduce)
    _seat("offr_s1", (-5, 4, -3)),
    _seat("offr_s2", (5, 11.5, -14.5)),
    _seat("offr_s3", (-5, 3.5, -18.9)),
    # hitbox-urile de click: șofer + 3 pasageri
    _inter("offr_i0", (5, 4, -3), "driver", w=1.0, h=1.4),
    _inter("offr_i1", (-5, 4, -3), "seat"),
    _inter("offr_i2", (5, 11.5, -14.5), "seat"),
    _inter("offr_i3", (-5, 3.5, -18.9), "seat"),
]

# parametri de condus (din mod / echivalențe)
ENGINE_PITCH_MIN = 0.8      # mod: minEnginePitch
ENGINE_PITCH_MAX = 1.6      # mod: maxEnginePitch
MAX_STEER_DEG = 35          # mod: DEFAULT_MAX_STEERING_ANGLE
FUEL_MAX = 600              # mod: energyCapacity 25000, redus pt. gameplay
FUEL_JERRY = 120            # bidonul umple 20%
SPEED_CRUISE = 0.3375       # attribute movement_speed (cal)
SPEED_BOOST = 0.55
