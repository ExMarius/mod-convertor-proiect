#!/usr/bin/env python3
"""Verificare 1:1 — simulează FIZICA MODULUI (LandVehicleEntity) și FIZICA
PLUGINULUI (OffroaderPlugin v2.0) cu aceiași inputi și compar traiectoriile."""
import math

# --- comune (off_roader.json + defaults) ---
ENGINE = 16.0; ACCEL = 0.05; REV = 0.4; MAX_REV = 5.0
DRAG = 0.001; BRAKE = 1.0; LIMIT = 100.0; MAX_STEER = 35.0
F_AXLE = (0.1 + 14.5) * 0.0625 * 1.4   # 1.2775
R_AXLE = (0.1 - 14.5) * 0.0625 * 1.4   # -1.26
SURF_FRIC = 0.9 * 1.1                    # SOLID × STANDARD road
SURF_TRAC = 1.0                          # SOLID
WHEEL_BASE = 0.8; WHEEL_SLIDE = 0.05

def yrot(x, z, a):  # vanilla Vector3d.yRot
    c, s = math.cos(a), math.sin(a)
    return x * c + z * s, z * c - x * s

def fwd_of(yaw):
    r = math.radians(yaw)
    return -math.sin(r), math.cos(r)

def yaw_of(x, z):
    return math.degrees(math.atan2(-x, z))

def wrap(a):
    while a > 180: a -= 360
    while a < -180: a += 360
    return a

def clamp(v, a, b): return max(a, min(b, v))

def lerp(a, b, t): return a + (b - a) * t

# ================= FIZica MODULUI (transcriere LandVehicleEntity) =================
def sim_mod(ticks_input, x=0.0, z=0.0, yaw=0.0, verbose=True):
    vx = vz = 0.0            # this.velocity
    traction = WHEEL_BASE
    traj = []
    for t, (turn, throttle, handbrake, boosting) in enumerate(ticks_input):
        fx, fz = fwd_of(yaw)
        # steering (VehicleHelper.getSteeringAngle, stocat între tick-uri)
        strength = 0.05 if turn != 0 else 0.2
        steer = steer_prev = globals().get('_mod_steer', 0.0)
        steer = steer + (MAX_STEER * turn - steer) * strength
        globals()['_mod_steer'] = steer
        # forțe
        force = ENGINE * clamp(throttle, -1, 1)
        if boosting: force += force * 0.5
        if throttle < 0: force *= REV
        ax = fx * force * ACCEL; az = fz * force * ACCEL
        if math.hypot(vx, vz) < 0.05: vx = vz = 0.0
        hb = vx * (BRAKE if handbrake else 0) * ACCEL, vz * (BRAKE if handbrake else 0) * ACCEL
        fr = vx * -SURF_FRIC * ACCEL, vz * -SURF_FRIC * ACCEL
        dr = vx * math.hypot(vx, vz) * -DRAG * ACCEL, vz * math.hypot(vx, vz) * -DRAG * ACCEL
        vx += ax + hb[0] + fr[0] + dr[0]; vz += az + hb[1] + fr[1] + dr[1]
        sp = math.hypot(vx, vz)
        if sp > LIMIT: vx *= LIMIT / sp; vz *= LIMIT / sp; sp = LIMIT
        # tracțiune
        speed = math.hypot(vx, vz)
        vxn = vx / speed if speed > 1e-9 else 0; vzn = vz / speed if speed > 1e-9 else 0
        cross = abs(fx * vzn - fz * vxn)
        sliding = cross >= 0.3
        if sliding and throttle > 0: traction = WHEEL_SLIDE
        elif handbrake: traction = WHEEL_SLIDE
        else:
            al = math.hypot(ax, az)
            target = WHEEL_BASE * clamp(speed / al, 0, 1) if al > 0 else WHEEL_BASE
            side = clamp(1 - cross / 0.3, 0, 1)
            traction = traction + (target - traction) * side * 0.15
        st = SURF_TRAC * traction
        # model bicicletă
        fw = (x + fx * F_AXLE, z + fz * F_AXLE)
        rw = (x + fx * R_AXLE, z + fz * R_AXLE)
        sv = yrot(vx, vz, math.radians(steer))
        fw = (fw[0] + sv[0] * ACCEL, fw[1] + sv[1] * ACCEL)
        rw = (rw[0] + vx * ACCEL, rw[1] + vz * ACCEL)
        hx, hz = fw[0] - rw[0], fw[1] - rw[1]
        hl = math.hypot(hx, hz)
        if hl > 1e-9: hx /= hl; hz /= hl
        else: hx, hz = fx, fz
        nx = rw[0] + hx * (-R_AXLE); nz = rw[1] + hz * (-R_AXLE)
        mx = nx - x; mz = nz - z
        dyaw = wrap(yaw_of(fx, fz) - yaw_of(hx, hz))
        yaw -= dyaw
        # viteză spre heading
        if speed > 0:
            if hx * vxn + hz * vzn >= 0: tx, tz = hx * speed, hz * speed
            else:
                rv = min(speed, MAX_REV); tx, tz = -hx * rv, -hz * rv
            vx = lerp(vx, tx, st); vz = lerp(vz, tz, st)
        x += mx; z += mz
        if t % 20 == 0 or t == len(ticks_input) - 1:
            traj.append((t, x, z, yaw, math.hypot(vx, vz) * 0.05 * 20 * 3.6))
    return traj

# ================= Fizica PLUGINULUI (transcriere OffroaderPlugin.drive) =================
def sim_plugin(ticks_input, x=0.0, z=0.0, yaw=0.0):
    vx = vz = 0.0
    steer = 0.0
    traction = WHEEL_BASE
    traj = []
    for t, (turn, throttle, handbrake, boosting) in enumerate(ticks_input):
        fx, fz = fwd_of(yaw)
        strength = 0.05 if turn != 0 else 0.2
        steer += (MAX_STEER * turn - steer) * strength
        force = ENGINE * clamp(throttle, -1, 1)
        if boosting: force += force * 0.5
        if throttle < 0: force *= REV
        sp0 = math.hypot(vx, vz)
        ax = fx * force * ACCEL; az = fz * force * ACCEL
        if sp0 < 0.05: vx = vz = 0
        hb = (vx * (BRAKE if handbrake else 0) * ACCEL, vz * (BRAKE if handbrake else 0) * ACCEL)
        fr = (vx * -SURF_FRIC * ACCEL, vz * -SURF_FRIC * ACCEL)
        dr = (vx * sp0 * -DRAG * ACCEL, vz * sp0 * -DRAG * ACCEL)
        vx += ax + hb[0] + fr[0] + dr[0]; vz += az + hb[1] + fr[1] + dr[1]
        speed = math.hypot(vx, vz)
        if speed > LIMIT: vx *= LIMIT / speed; vz *= LIMIT / speed; speed = LIMIT
        vxn = vx / speed if speed > 1e-9 else 0; vzn = vz / speed if speed > 1e-9 else 0
        cross = abs(fx * vzn - fz * vxn)
        sliding = cross >= 0.3
        if sliding and throttle > 0: traction = WHEEL_SLIDE
        elif handbrake: traction = WHEEL_SLIDE
        else:
            al = math.hypot(ax, az)
            target = WHEEL_BASE * clamp(speed / al, 0, 1) if al > 0 else WHEEL_BASE
            side = clamp(1 - cross / 0.3, 0, 1)
            traction = traction + (target - traction) * side * 0.15
        st = SURF_TRAC * traction
        front = (fx * F_AXLE + yrot(vx, vz, math.radians(steer))[0] * ACCEL,
                 fz * F_AXLE + yrot(vx, vz, math.radians(steer))[1] * ACCEL)
        rear = (fx * R_AXLE + vx * ACCEL, fz * R_AXLE + vz * ACCEL)
        hx, hz = front[0] - rear[0], front[1] - rear[1]
        hl = math.hypot(hx, hz)
        if hl > 1e-9: hx /= hl; hz /= hl
        else: hx, hz = fx, fz
        mx = rear[0] + hx * (-R_AXLE); mz = rear[1] + hz * (-R_AXLE)
        dYaw = wrap(yaw_of(fx, fz) - yaw_of(hx, hz))
        yaw -= dYaw
        if speed > 0:
            if hx * vxn + hz * vzn >= 0: tX, tZ = hx * speed, hz * speed
            else:
                rv = min(speed, MAX_REV); tX, tZ = -hx * rv, -hz * rv
            vx += (tX - vx) * st; vz += (tZ - vz) * st
        x += mx; z += mz
        if t % 20 == 0 or t == len(ticks_input) - 1:
            traj.append((t, x, z, yaw, math.hypot(vx, vz) * 0.05 * 20 * 3.6))
    return traj

# ---- scenarii ----
def scen(n, turn=0, throttle=1, hb=0, boost=0):
    return [(turn, throttle, hb, boost)] * n

print("=== S1: W 6s (accelerare 0→top) ===")
a = sim_mod(scen(120)); globals()['_mod_steer'] = 0.0
b = sim_plugin(scen(120))
for r1, r2 in zip(a, b):
    d = math.hypot(r1[1] - r2[1], r1[2] - r2[2])
    print(f"  t={r1[0]:3d}  mod: pos=({r1[1]:7.2f},{r1[2]:7.2f}) yaw={r1[3]:7.1f} {r1[4]:5.1f}km/h   plugin: pos=({r2[1]:7.2f},{r2[2]:7.2f}) yaw={r2[3]:7.1f} {r2[4]:5.1f}km/h   Δ={d:.4f}")

print("=== S2: W + A (viraj stânga) 6s ===")
a = sim_mod(scen(120, turn=1)); globals()['_mod_steer'] = 0.0
b = sim_plugin(scen(120, turn=1))
for r1, r2 in zip(a, b):
    d = math.hypot(r1[1] - r2[1], r1[2] - r2[2])
    print(f"  t={r1[0]:3d}  mod: pos=({r1[1]:7.2f},{r1[2]:7.2f}) yaw={r1[3]:7.1f}   plugin: pos=({r2[1]:7.2f},{r2[2]:7.2f}) yaw={r2[3]:7.1f}   Δ={d:.4f}")

print("=== S3: W 4s apoi W+SPAȚIU (frână mână) 2s ===")
inp = scen(80) + scen(40, hb=1)
a = sim_mod(inp); globals()['_mod_steer'] = 0.0
b = sim_plugin(inp)
for r1, r2 in zip(a, b):
    print(f"  t={r1[0]:3d}  mod: {r1[4]:5.1f}km/h pos=({r1[1]:7.2f},{r1[2]:7.2f})   plugin: {r2[4]:5.1f}km/h pos=({r2[1]:7.2f},{r2[2]:7.2f})")

print("=== S4: marșarier S 3s ===")
a = sim_mod(scen(60, throttle=-1)); globals()['_mod_steer'] = 0.0
b = sim_plugin(scen(60, throttle=-1))
for r1, r2 in zip(a, b):
    print(f"  t={r1[0]:3d}  mod: {r1[4]:5.1f}km/h   plugin: {r2[4]:5.1f}km/h")
