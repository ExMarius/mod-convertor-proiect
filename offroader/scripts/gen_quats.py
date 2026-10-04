"""
Generează datapack/data/offroader/function/veh/init_quats.mcfunction:
tabele de quaternioni în storage, folosite pentru rotirea display-urilor.

yaw[i]  (i = 0..35): rotație în jurul axei Y cu -10*i grade.
  Derivare: fața modelului = -Z; direcția calului f(y)=(−sin y, cos y);
  unghiul de rotație necesar = 180−y; indexul i = ((y+180) mod 360)/10
  => unghi = −10*i.
  Dacă în joc mașina merge cu spatele: /scoreboard players set #flip offr.dummy 1
  (follow.mcfunction adaugă +18 la index = +180°).

spin[j] (j = 0..23): rotație în jurul axei X cu -15*j grade (rotire înainte).
  Dacă rotile se învârt invers: /scoreboard players set #spinflip offr.dummy 1
"""
import math
import os
import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
FUNC = os.path.join(HERE, "..", "datapack", "data", C.NS, "function", "veh")


def quat_y(deg):
    """Quaternion axa-unghi standard pentru rotația de «deg» grade în jurul lui Y."""
    a = math.radians(deg) / 2
    return [0.0, math.sin(a), 0.0, math.cos(a)]


def quat_x(deg):
    """Quaternion axa-unghi standard pentru rotația de «deg» grade în jurul lui X."""
    a = math.radians(deg) / 2
    return [math.sin(a), 0.0, 0.0, math.cos(a)]


def fmt(q):
    return "[" + ",".join(f"{v:.6f}f" for v in q) + "]"


if __name__ == "__main__":
    yaw = [fmt(quat_y(-10 * i)) for i in range(36)]
    spin = [fmt(quat_x(-15 * j)) for j in range(24)]
    line_yaw = "data merge storage offroader:quats {yaw:[" + ",".join(yaw) + "]}"
    line_spin = "data merge storage offroader:quats {spin:[" + ",".join(spin) + "]}"
    os.makedirs(FUNC, exist_ok=True)
    with open(os.path.join(FUNC, "init_quats.mcfunction"), "w") as f:
        f.write("# Generat de gen_quats.py — nu edita manual.\n")
        f.write(line_yaw + "\n")
        f.write(line_spin + "\n")
    print("init_quats.mcfunction generat:",
          f"{len(yaw)} yaw + {len(spin)} spin quaternioni")
