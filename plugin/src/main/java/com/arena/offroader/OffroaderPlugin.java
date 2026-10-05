package com.arena.offroader;

import io.papermc.paper.entity.TeleportFlag;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.SoundCategory;
import org.bukkit.World;
import org.bukkit.block.Block;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Horse;
import org.bukkit.entity.Player;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerQuitEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.potion.PotionEffect;
import org.bukkit.potion.PotionEffectType;
import org.bukkit.scheduler.BukkitRunnable;
import org.bukkit.util.BoundingBox;
import org.bukkit.util.Vector;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * OffroaderPlugin v2.0 — port COMPLET 1:1 al offroader-ului din
 * MrCrayfish's Vehicle Mod (1.16.X), rulat 100% pe server (client vanilla).
 *
 * Fizica este transcrierea exactă a LandVehicleEntity.updateVehicleMotion():
 *
 *   UNITĂȚI: viteza e în unități mod; deplasarea/tick = v × 0.05 (blocuri).
 *   accel       = fwd × enginePower(16) × throttle × 0.05   (reverse ×0.4)
 *   boost       = forța + forța×0.5, 10 tick-i cât timp W e apăsat
 *   fricțiune   = v × (−surfaceFriction) × 0.05
 *                 SOLID 0.99 · DIRT 1.43 · ZĂPADĂ 2.55 · GHEAȚĂ 1.5
 *   drag        = v × |v| × (−0.001) × 0.05
 *   frână mână  = v × (−1.0) × 0.05 + throttle 0      (SPAȚIU)
 *   tracțiune   = roți STANDARD: bază 0.8, alunecare 0.05
 *                 frână mână sau drift → 0.05 (MAȘINA ALUNECĂ)
 *                 altfel lerp 0.15 × side spre 0.8×clamp(|v|/|a|)
 *   suprafață   = factor tracțiune: SOLID 1.0 · DIRT 0.9 · ZĂPADĂ 0.9 · GHEAȚĂ 0.01
 *   viteză max  = 100 unități (globalSpeedLimit; ~63 km/h efectiv)
 *   model bicicletă:
 *     față = pos + fwd×1.2775 + rot(v, steer)×0.05
 *     spate = pos + fwd×(−1.26) + v×0.05
 *     heading = norm(față−spate); pos' = spate + heading×1.26
 *     yaw −= wrapDeg(yaw(fwd) − yaw(heading))
 *   gravitație  = −0.08/tick pe delta; la sol delta ×(0.75, 0, 0.75)
 *   combustibil = 25000 (consum 0.25/tick cu șofer; bidon +5000)
 *   motor       = start.ogg la urcare, engine.ogg în buclă cu pitch
 *                 0.8 + 0.8×|v|/25, stop.ogg la coborâre
 *
 * Calul invizibil = „motorul" (hitbox + șofer); pluginul îi controlează
 * exact mișcarea: teleport cu pasageri în fiecare tick (clientul interpolează).
 * Caroseria/roțile/scaunele rămân poziționate de datapack (veh/follow).
 */
public final class OffroaderPlugin extends JavaPlugin implements Listener {

    // ---- constante 1:1 (LandVehicleEntity / PoweredVehicleEntity / off_roader.json / WheelType.STANDARD) ----
    private static final float ENGINE_POWER   = 16.0f;   // large_motor, tier iron ×1.0
    private static final float ACCEL          = 0.05f;
    private static final float REVERSE_FACTOR = 0.4f;
    private static final float MAX_REVERSE    = 5.0f;
    private static final float DRAG           = 0.001f;
    private static final float BRAKE_POWER    = 1.0f;    // DEFAULT_BRAKE_POWER
    private static final float GLOBAL_LIMIT   = 100.0f;  // Config.SERVER.globalSpeedLimit (unități)
    private static final float MAX_STEER      = 35.0f;   // DEFAULT_MAX_STEERING_ANGLE
    private static final float BOOST_SPEED_MULTIPLIER = 0.5f; // setBoosting: forwardForce += ×0.5
    private static final int   BOOST_TICKS    = 10;      // setBoosting: boostTimer = 10
    private static final float GRAVITY        = 0.08f;
    private static final float WHEEL_BASE_TRACTION = 0.8f;   // STANDARD
    private static final float WHEEL_SLIDE_TRACTION = 0.05f; // STANDARD
    private static final double FRONT_AXLE = (0.1 + 14.5) * 0.0625 * 1.4;  // 1.2775
    private static final double REAR_AXLE  = (0.1 - 14.5) * 0.0625 * 1.4;  // −1.26
    private static final float PITCH_MIN = 0.8f, PITCH_MAX = 1.6f;         // off_roader.json
    private static final int FUEL_MAX_QUARTER = 100000;  // 25000 × 4 (scorul e în sferturi)
    private static final int ENGINE_LOOP_TICKS = 19;     // engine.ogg = 1.0s
    // hitbox din ModEntities: OFF_ROADER = 2.0F × 1.0F; step ca în mod
    private static final double VEH_WIDTH = 2.0, VEH_HEIGHT = 1.0, STEP_HEIGHT = 1.0, EPS = 1.0E-7;

    /** stare per vehicul (unități mod) */
    private static final class Veh {
        double vx, vz;            // velocity (unități)
        float steering;           // unghi volan (grade)
        float traction = WHEEL_BASE_TRACTION;
        double dx, dy, dz;        // deltaMovement (gravitație/inerție)
        boolean engineOn;         // motorul merge (pt start/stop.ogg)
        int soundCd;              // cadența buclei motorului
        int hornCd;
        boolean grounded;       // onGround din mod (motorul trage doar la sol)
    }

    private final Map<UUID, Veh> state = new HashMap<>();
    private final NamespacedKey keyItem, wheelItem, canItem, initKey;

    public OffroaderPlugin() {
        keyItem   = NamespacedKey.fromString("offroader:key");
        wheelItem = NamespacedKey.fromString("offroader:steering_wheel");
        canItem   = NamespacedKey.fromString("offroader:jerrycan");
        initKey   = new NamespacedKey(this, "init");
    }

    @Override
    public void onEnable() {
        getLogger().info("OffroaderPlugin v2.1 activ — port complet 1:1 din Vehicle Mod (fizică + sunete + combustibil).");
        Bukkit.getPluginManager().registerEvents(this, this);
        setPluginFlag(1);
        Bukkit.getScheduler().runTaskTimer(this, this::tick, 1L, 1L);
    }

    @Override
    public void onDisable() {
        setPluginFlag(0);
    }

    /** marchează modul plugin în scoreboard (datapack-ul își dezactivează fizica proprie) */
    private void setPluginFlag(int v) {
        var obj = Bukkit.getScoreboardManager().getMainScoreboard().getObjective("offr.dummy");
        if (obj != null) obj.getScore("#plugin").setScore(v);
        else Bukkit.dispatchCommand(Bukkit.getConsoleSender(),
                "scoreboard objectives add offr.dummy dummy");
    }

    // ------------------------------------------------------------------ tick

    private void tick() {
        // re-asigură flagul (load.mcfunction îl resetează la /reload)
        var obj = Bukkit.getScoreboardManager().getMainScoreboard().getObjective("offr.dummy");
        if (obj == null || obj.getScore("#plugin").getScore() != 1) setPluginFlag(1);

        for (var world : Bukkit.getWorlds()) {
            for (Entity e : new ArrayList<>(world.getEntitiesByClass(Horse.class))) {
                if (!e.getScoreboardTags().contains("offr_veh")) continue;
                Horse horse = (Horse) e;
                try {
                    drive(horse);
                } catch (Exception ex) {
                    getLogger().warning("tick " + horse.getUniqueId() + ": " + ex);
                }
            }
        }
    }

    private void drive(Horse horse) {
        UUID id = horse.getUniqueId();
        Veh v = state.computeIfAbsent(id, k -> new Veh());

        // prima oară văzut de plugin: rezervor plin (25000, în sferturi pe scor)
        var pdc = horse.getPersistentDataContainer();
        if (!pdc.has(initKey, PersistentDataType.BYTE)) {
            pdc.set(initKey, PersistentDataType.BYTE, (byte) 1);
            setScore(horse, "offr.fuel", FUEL_MAX_QUARTER);
            horse.setAI(false);                 // NoAI mereu — pluginul mută calul prin teleport
            horse.setInvulnerable(true);
        }

        Player driver = null;
        for (Entity p : horse.getPassengers()) if (p instanceof Player pl) { driver = pl; break; }

        // ---- input (mod: A/D = volan, W/S = accelerație, SPAȚIU = frână mână, SHIFT = cobori) ----
        float turn = 0f;
        double throttle = 0;
        boolean handbrake = false;
        if (driver != null) {
            var in = driver.getCurrentInput();
            if (in.isLeft())  turn += 1f;
            if (in.isRight()) turn -= 1f;
            if (in.isForward())  throttle += 1;
            if (in.isBackward()) throttle -= 1;
            handbrake = in.isJump();
            if (handbrake) throttle = 0;
            if (in.isSneak()) {                       // SHIFT = coboară din mașină
                horse.removePassenger(driver);
                driver = null;
            }
        }

        // fără șofer: volanul revine (×0.85), motorul oprit, mașina frânată natural
        if (driver == null) {
            v.steering *= 0.85f;
            throttle = 0;
        }

        // ---- combustibil (scorul offr.fuel e în sferturi de unitate) ----
        int fuel = score(horse, "offr.fuel");
        if (fuel <= 0 && driver != null && throttle > 0) {
            throttle = 0;                              // mod: motorul moare fără energie
            actionbar(driver, "§c§lFĂRĂ COMBUSTIBIL! §7Alimentează cu bidonul.");
        }
        boolean boostScore = score(horse, "offr.boost") > 0;
        int boost = Math.max(0, score(horse, "offr.boost"));

        // ---- motor: pornit/oprit + consum 0.25/tick ----
        boolean engineOn = driver != null && fuel > 0;
        if (engineOn && driver != null && !driver.getGameMode().equals(org.bukkit.GameMode.CREATIVE)) {
            setScore(horse, "offr.fuel", fuel - 1);    // 1 sfert = 0.25/tick
            fuel -= 1;
        }
        if (engineOn && !v.engineOn) {                 // pornire
            play(horse, "offroader:start", 1.2f, 1f);
            v.engineOn = true;
        } else if (!engineOn && v.engineOn) {          // oprire
            play(horse, "offroader:stop", 0.8f, 1f);
            v.engineOn = false;
        }

        // ---- boost (volan click-dreapta): forța ×1.5, 10 tick-i cât timp W ----
        boolean boosting = false;
        if (boost > 0) {
            if (throttle > 0) { boosting = true; boost--; }
            else boost = 0;
            setScore(horse, "offr.boost", boost);
        }

        // ---- steering: rampa exactă VehicleHelper.getSteeringAngle ----
        float strength = (turn != 0f) ? 0.05f : 0.2f;
        v.steering += (MAX_STEER * turn - v.steering) * strength;

        // ---- dinamica (unități mod) ----
        // mod: enginePower și brakePower doar LA SOL (isOnGround ? val : 0)
        double yawDeg = horse.getLocation().getYaw();
        double r = Math.toRadians(yawDeg);
        double[] fwd = {-Math.sin(r), Math.cos(r)};

        double force = v.grounded ? ENGINE_POWER * clamp(throttle, -1, 1) : 0;
        if (boosting) force += force * BOOST_SPEED_MULTIPLIER;
        if (throttle < 0) force *= REVERSE_FACTOR;

        double speed = Math.hypot(v.vx, v.vz);
        double[] accel = {fwd[0] * force * ACCEL, fwd[1] * force * ACCEL};
        if (speed < 0.05) { v.vx = 0; v.vz = 0; speed = 0; }

        // suprafața sub punți (SOLID/DIRT/ZĂPADĂ/GHEAȚĂ) — WheelType.STANDARD
        float surfFriction = surfaceFriction(horse, fwd);
        float surfTractionFactor = surfaceTractionFactor(horse, fwd);

        double[] hb   = {v.vx * (handbrake && v.grounded ? BRAKE_POWER : 0) * ACCEL, v.vz * (handbrake && v.grounded ? BRAKE_POWER : 0) * ACCEL};
        double[] fric = {v.vx * -surfFriction * ACCEL, v.vz * -surfFriction * ACCEL};
        double[] dragF= {v.vx * speed * -DRAG * ACCEL, v.vz * speed * -DRAG * ACCEL};
        v.vx += accel[0] + hb[0] + fric[0] + dragF[0];
        v.vz += accel[1] + hb[1] + fric[1] + dragF[1];
        speed = Math.hypot(v.vx, v.vz);
        if (speed > GLOBAL_LIMIT) { v.vx *= GLOBAL_LIMIT / speed; v.vz *= GLOBAL_LIMIT / speed; speed = GLOBAL_LIMIT; }

        // ---- tracțiune / drift (LandVehicleEntity) ----
        double vxn = speed > 1e-9 ? v.vx / speed : 0, vzn = speed > 1e-9 ? v.vz / speed : 0;
        double cross = Math.abs(fwd[0] * vzn - fwd[1] * vxn);      // |v̂ × f̂|
        boolean sliding = cross >= 0.3;
        if (sliding && throttle > 0) {
            v.traction = WHEEL_SLIDE_TRACTION;
        } else if (handbrake) {
            v.traction = WHEEL_SLIDE_TRACTION;
        } else {
            double al = Math.hypot(accel[0], accel[1]);
            float target = al > 0 ? (float) (WHEEL_BASE_TRACTION * clamp(speed / al, 0, 1)) : WHEEL_BASE_TRACTION;
            float side = (float) clamp(1 - cross / 0.3, 0, 1);
            v.traction = v.traction + (target - v.traction) * side * 0.15f;
        }
        float surfaceTraction = surfTractionFactor * v.traction;

        // ---- modelul bicicletă ----
        double[] front = {fwd[0] * FRONT_AXLE, fwd[1] * FRONT_AXLE};
        double[] rear  = {fwd[0] * REAR_AXLE,  fwd[1] * REAR_AXLE};
        double sr = Math.toRadians(v.steering);
        double cs = Math.cos(sr), sn = Math.sin(sr);
        double svx = v.vx * cs + v.vz * sn, svz = v.vz * cs - v.vx * sn;   // yRot(v, steer)
        front[0] += svx * ACCEL; front[1] += svz * ACCEL;
        rear[0]  += v.vx * ACCEL; rear[1]  += v.vz * ACCEL;

        double hx = front[0] - rear[0], hz = front[1] - rear[1];
        double hl = Math.hypot(hx, hz);
        if (hl > 1e-9) { hx /= hl; hz /= hl; } else { hx = fwd[0]; hz = fwd[1]; }

        double mx = rear[0] + hx * (-REAR_AXLE);   // mișcarea acestui tick (blocuri)
        double mz = rear[1] + hz * (-REAR_AXLE);

        // yaw: yRot -= wrapDegrees(yaw(fwd) − yaw(heading))
        double yawF = Math.toDegrees(Math.atan2(-fwd[0], fwd[1]));
        double yawH = Math.toDegrees(Math.atan2(-hx, hz));
        double dYaw = yawF - yawH;
        while (dYaw > 180) dYaw -= 360;
        while (dYaw < -180) dYaw += 360;
        float newYaw = (float) (yawDeg - dYaw);

        // viteza urmărește heading-ul (cu tracțiunea suprafeței → drift pe frână/gheață)
        if (speed > 0) {
            double dot = hx * vxn + hz * vzn;
            double tX, tZ;
            if (dot >= 0) { tX = hx * speed; tZ = hz * speed; }
            else { double rev = Math.min(speed, MAX_REVERSE); tX = -hx * rev; tZ = -hz * rev; }
            v.vx += (tX - v.vx) * surfaceTraction;
            v.vz += (tZ - v.vz) * surfaceTraction;
        }

        // ---- gravitația + coliziuni + aplicare prin teleport (ca Entity.move din mod) ----
        v.dy -= GRAVITY;

        Location hloc = horse.getLocation();
        double[] mv = collideMove(horse.getWorld(), hloc, mx, v.dy, mz, v.grounded);
        boolean onGround = mv[3] >= 1.0;

        boolean needMove = Math.abs(mv[0]) + Math.abs(mv[1]) + Math.abs(mv[2]) > 1e-9
                || Math.abs(dYaw) > 1e-4 || !v.grounded;
        if (needMove) {
            // teleport CU pasageri → clientul interpolează (echivalentul
            // updateInterval=1 + velocityUpdates din ModEntities)
            Location target = new Location(horse.getWorld(),
                    hloc.getX() + mv[0], hloc.getY() + mv[1], hloc.getZ() + mv[2], newYaw, 0f);
            horse.teleport(target, TeleportFlag.EntityState.RETAIN_PASSENGERS);
        }
        v.grounded = onGround;

        if (driver == null) {                          // parcat: fără inerție reziduală
            v.dx = 0; v.dz = 0;
            if (Math.abs(v.vx) + Math.abs(v.vz) < 0.05) { v.vx = 0; v.vz = 0; }
        }
        if (onGround) {                                // mod: sol → delta ×(0.75, 0, 0.75)
            v.dx *= 0.75; v.dy = 0; v.dz *= 0.75;
        } else {                                       // aer → ×(0.98, 1, 0.98)
            v.dx *= 0.98; v.dz *= 0.98;
        }

        // ---- sunet de motor în buclă (pitch 0.8 + 0.8×|v|/25) ----
        if (engineOn && --v.soundCd <= 0) {
            v.soundCd = ENGINE_LOOP_TICKS;
            play(horse, "offroader:engine", 1.0f, PITCH_MIN + (PITCH_MAX - PITCH_MIN) * (float) Math.min(speed / 25.0, 1.0));
        }
        if (v.hornCd > 0) v.hornCd--;

        // ---- fum de eșapament (exhaustFumesPosition ~ originea vehiculului) ----
        if (engineOn && Math.random() < 0.4) {
            var loc = horse.getLocation().add(0, 0.4, 0);
            horse.getWorld().spawnParticle(org.bukkit.Particle.SMOKE, loc, 2, 0.1, 0.05, 0.1, 0.005);
        }

        // ---- HUD (șofer): combustibil + viteză km/h + stare ----
        if (driver != null && horse.getTicksLived() % 5 == 0) {
            double kmh = speed * 3.6;                 // v unități = m/s (v×0.05 b/tick × 20)
            int pct = Math.max(0, Math.min(100, fuel * 100 / FUEL_MAX_QUARTER));
            StringBuilder sb = new StringBuilder("§6⛽ ");
            int seg = (pct * 12) / 100;
            for (int i = 0; i < 12; i++) sb.append(i < seg ? (pct < 20 ? "§c▌" : "§a▌") : "§8▌");
            sb.append("§r ").append(pct).append("%  §b").append(Math.round(kmh)).append(" km/h");
            if (boosting) sb.append("  §4§lBOOST!");
            else if (sliding || (handbrake && speed > 2)) sb.append("  §d§lDRIFT");
            actionbar(driver, sb.toString());
        }
    }

    // ------------------------------------------------ coliziuni (Entity.move din mod: 2.0×1.0, step 1.0)

    /** decupează mișcarea pe o axă contra box-urilor solide (algoritmul vanilla) */
    private static double clipAxis(java.util.List<BoundingBox> solids, BoundingBox self, double d, char axis) {
        for (BoundingBox b : solids) {
            boolean yOv = self.getMaxY() > b.getMinY() + EPS && self.getMinY() < b.getMaxY() - EPS;
            boolean zOv = self.getMaxZ() > b.getMinZ() + EPS && self.getMinZ() < b.getMaxZ() - EPS;
            boolean xOv = self.getMaxX() > b.getMinX() + EPS && self.getMinX() < b.getMaxX() - EPS;
            if (axis == 'x' && yOv && zOv) {
                if (d > 0 && self.getMaxX() <= b.getMinX() + EPS) d = Math.min(d, b.getMinX() - self.getMaxX());
                else if (d < 0 && self.getMinX() >= b.getMaxX() - EPS) d = Math.max(d, b.getMaxX() - self.getMinX());
            } else if (axis == 'y' && xOv && zOv) {
                if (d > 0 && self.getMaxY() <= b.getMinY() + EPS) d = Math.min(d, b.getMinY() - self.getMaxY());
                else if (d < 0 && self.getMinY() >= b.getMaxY() - EPS) d = Math.max(d, b.getMaxY() - self.getMinY());
            } else if (axis == 'z' && xOv && yOv) {
                if (d > 0 && self.getMaxZ() <= b.getMinZ() + EPS) d = Math.min(d, b.getMinZ() - self.getMaxZ());
                else if (d < 0 && self.getMinZ() >= b.getMaxZ() - EPS) d = Math.max(d, b.getMaxZ() - self.getMinZ());
            }
        }
        return d;
    }

    /** toate box-urile de coliziune din zona măturată de mișcare */
    private static java.util.List<BoundingBox> solidsNear(World w, double x0, double y0, double z0,
                                                          double x1, double y1, double z1) {
        java.util.List<BoundingBox> out = new ArrayList<>();
        int bx0 = (int) Math.floor(Math.min(x0, x1)) - 1, bx1 = (int) Math.floor(Math.max(x0, x1)) + 1;
        int by0 = (int) Math.floor(Math.min(y0, y1)) - 2, by1 = (int) Math.floor(Math.max(y0, y1)) + 2;
        int bz0 = (int) Math.floor(Math.min(z0, z1)) - 1, bz1 = (int) Math.floor(Math.max(z0, z1)) + 1;
        for (int x = bx0; x <= bx1; x++)
            for (int y = by0; y <= by1; y++)
                for (int z = bz0; z <= bz1; z++) {
                    Block blk = w.getBlockAt(x, y, z);
                    if (blk.isEmpty() || blk.isLiquid()) continue;
                    for (BoundingBox cb : blk.getCollisionShape().getBoundingBoxes())
                        if (cb.getWidthX() > 0 && cb.getHeight() > 0 && cb.getWidthZ() > 0) out.add(cb);
                }
        return out;
    }

    /** mișcare cu coliziuni per-axă + step-up 1.0 → {dx, dy, dz, grounded} */
    private double[] collideMove(World w, Location loc, double mx, double my, double mz, boolean wasGround) {
        double x = loc.getX(), y = loc.getY(), z = loc.getZ();
        java.util.List<BoundingBox> solids = solidsNear(w, x, y, z, x + mx, y + Math.min(my, -STEP_HEIGHT), z + mz);

        BoundingBox box = new BoundingBox(x - VEH_WIDTH / 2, y, z - VEH_WIDTH / 2,
                x + VEH_WIDTH / 2, y + VEH_HEIGHT, z + VEH_WIDTH / 2);

        // traiectul normal: Y, X, Z (ordinea din Entity.collide)
        double dy = clipAxis(solids, box, my, 'y');
        BoundingBox b1 = box.clone().shift(new Vector(0, dy, 0));
        double dx = clipAxis(solids, b1, mx, 'x');
        b1 = b1.clone().shift(new Vector(dx, 0, 0));
        double dz = clipAxis(solids, b1, mz, 'z');
        boolean grounded = my < 0 && dy != my;

        // step-up (maxUpStep = 1.0 exact ca în mod): ridică, orizontal, coboară pe treaptă
        if ((Math.abs(dx - mx) > 1e-6 || Math.abs(dz - mz) > 1e-6) && (wasGround || grounded)) {
            BoundingBox up = box.clone().shift(new Vector(0, STEP_HEIGHT, 0));
            double sdx = clipAxis(solids, up, mx, 'x');
            up = up.clone().shift(new Vector(sdx, 0, 0));
            double sdz = clipAxis(solids, up, mz, 'z');
            BoundingBox down = up.clone().shift(new Vector(0, 0, sdz));
            double sdy = clipAxis(solids, down, -STEP_HEIGHT, 'y');
            if (sdx * sdx + sdz * sdz > dx * dx + dz * dz + 1e-9)
                return new double[]{sdx, STEP_HEIGHT + sdy, sdz, 1.0};
        }
        return new double[]{dx, dy, dz, grounded ? 1.0 : 0.0};
    }

    // ------------------------------------------------------------------ suprafețe (SurfaceHelper + WheelType.STANDARD)

    private static final int SURF_SOLID = 0, SURF_DIRT = 1, SURF_SNOW = 2, SURF_ICE = 3, SURF_NONE = 4;

    private int surfaceAt(Horse horse, double[] fwd, double axle) {
        var loc = horse.getLocation();
        var b = horse.getWorld().getBlockAt(
                loc.getBlockX() + (int) Math.floor(fwd[0] * axle),
                loc.getBlockY() - 1,
                loc.getBlockZ() + (int) Math.floor(fwd[1] * axle));
        Material m = b.getType();
        if (b.isLiquid() || m.isAir()) return SURF_NONE;
        if (m == Material.ICE || m == Material.PACKED_ICE || m == Material.BLUE_ICE || m == Material.FROSTED_ICE) return SURF_ICE;
        if (m.name().contains("SNOW") || m.name().contains("LEAVES") || m == Material.CACTUS) return SURF_SNOW;
        switch (m) {
            case GRASS_BLOCK: case DIRT: case COARSE_DIRT: case PODZOL: case ROOTED_DIRT:
            case MUD: case MUDDY_MANGROVE_ROOTS: case SAND: case RED_SAND: case GRAVEL:
            case CLAY: case FARMLAND: case DIRT_PATH: case MYCELIUM: case SOUL_SAND:
                return SURF_DIRT;
            default:
                if (m.name().contains("WOOL") || m.name().contains("CARPET")) return SURF_DIRT;
                return m.isSolid() ? SURF_SOLID : SURF_NONE;
        }
    }

    /** media pe punți, exact ca SurfaceHelper.getValue (roțile pe NONE se sar) */
    private float surfAvg(Horse horse, double[] fwd, float solid, float dirt, float snow, float ice) {
        int a = surfaceAt(horse, fwd, FRONT_AXLE), b = surfaceAt(horse, fwd, REAR_AXLE);
        float sum = 0; int n = 0;
        if (a != SURF_NONE) { sum += val(a, solid, dirt, snow, ice); n++; }
        if (b != SURF_NONE) { sum += val(b, solid, dirt, snow, ice); n++; }
        return n == 0 ? 0f : sum / n;
    }
    private static float val(int s, float solid, float dirt, float snow, float ice) {
        switch (s) {
            case SURF_SOLID: return solid;
            case SURF_DIRT:  return dirt;
            case SURF_SNOW:  return snow;
            case SURF_ICE:   return ice;
        }
        return 0;
    }
    private float surfaceFriction(Horse h, double[] fwd) {
        return surfAvg(h, fwd, 0.9f * 1.1f, 1.1f * 1.3f, 1.5f * 1.7f, 1.5f * 1.0f);
    }
    private float surfaceTractionFactor(Horse h, double[] fwd) {
        return surfAvg(h, fwd, 1.0f, 0.9f, 0.9f, 0.01f);
    }

    // ------------------------------------------------------------------ interacțiuni (itemele modului)

    @EventHandler
    public void onInteract(PlayerInteractEvent e) {
        if (e.getAction() != Action.RIGHT_CLICK_AIR && e.getAction() != Action.RIGHT_CLICK_BLOCK) return;
        Player p = e.getPlayer();
        NamespacedKey model = modelOf(e.getItem());
        if (model == null) return;

        // ---- CHEIA: claxon / depozitează / scoate mașina ----
        if (model.equals(keyItem)) {
            e.setCancelled(true);
            Horse veh = riddenVehicle(p);
            if (veh != null) { horn(veh); return; }                       // șofezi → claxon
            Entity seat = p.getVehicle();
            if (seat != null && seat.getScoreboardTags().contains("offr_seat")) {  // pasager → claxon
                play(seat, "offroader:horn", 1.2f, 1f);
                return;
            }
            Horse near = nearestVehicle(p, 5);
            if (near != null) {                     // depozitează
                console("execute as @e[type=minecraft:horse,tag=offr_veh,distance=..5,limit=1,sort=nearest] at @s run function offroader:veh/store");
            } else {                               // scoate una nouă
                console("execute as " + p.getName() + " at @s run function offroader:veh/spawn");
            }
            return;
        }

        // ---- VOLANUL: BOOST (click-dreapta în timp ce șofezi) ----
        if (model.equals(wheelItem)) {
            e.setCancelled(true);
            Horse veh = riddenVehicle(p);
            if (veh == null) return;
            if (score(veh, "offr.fuel") > 0) {
                setScore(veh, "offr.boost", BOOST_TICKS);
                play(veh, "offroader:boost", 1.6f, 1f);
                actionbar(p, "§4§lBOOST!");
            } else {
                play(veh, "offroader:stop", 0.8f, 1.6f);
                actionbar(p, "§cFără combustibil! Alimentează cu bidonul.");
            }
            return;
        }

        // ---- BIDONUL: alimentare +20% (5000 din 25000) ----
        if (model.equals(canItem)) {
            e.setCancelled(true);
            Horse veh = nearestVehicle(p, 5);
            if (veh == null) { actionbar(p, "§7Niciun offroader prin apropiere."); return; }
            int fuel = score(veh, "offr.fuel");
            fuel = Math.min(FUEL_MAX_QUARTER, fuel + 20000);
            setScore(veh, "offr.fuel", fuel);
            play(veh, "offroader:slosh", 1.0f, 1f);
            int pct = fuel * 100 / FUEL_MAX_QUARTER;
            actionbar(p, "§a⛽ Alimentat: " + pct + "% (+" + 5000 + ")");
        }
    }

    private void horn(Horse veh) {
        Veh v = state.get(veh.getUniqueId());
        if (v != null && v.hornCd > 0) return;
        if (v != null) v.hornCd = 15;
        play(veh, "offroader:horn", 1.2f, 1f);
    }

    // ------------------------------------------------------------------ kit la join

    @EventHandler
    public void onJoin(PlayerJoinEvent e) {
        if (e.getPlayer().getScoreboardTags().contains("offr_kit")) return;
        Bukkit.getScheduler().runTaskLater(this, () -> {
            if (e.getPlayer().isOnline()) giveKit(e.getPlayer());
        }, 20L);
    }

    @EventHandler
    public void onQuit(PlayerQuitEvent e) {
        // șoferul iese din joc → mașina rămâne; starea ei supraviețuiește
    }

    private void giveKit(Player p) {
        boolean ok = Bukkit.dispatchCommand(Bukkit.getConsoleSender(),
                "execute as " + p.getName() + " at @s run function offroader:give");
        if (ok) {
            p.addScoreboardTag("offr_kit");
            getLogger().info("kit offroader dat lui " + p.getName());
        } else {
            getLogger().warning("nu am putut da kitul lui " + p.getName() + " — datapack-ul offroader e încărcat?");
        }
    }

    @Override
    public boolean onCommand(CommandSender sender, Command cmd, String label, String[] args) {
        if (sender instanceof Player p) {
            giveKit(p);
            p.sendMessage("§e[Offroader] §aAi primit cheia, volanul și bidonul (dacă le-ai pierdut).");
            return true;
        }
        return false;
    }

    // ------------------------------------------------------------------ utilitare

    private Horse riddenVehicle(Player p) {
        Entity v = p.getVehicle();
        return (v instanceof Horse h && h.getScoreboardTags().contains("offr_veh")) ? h : null;
    }

    private Horse nearestVehicle(Player p, double dist) {
        Horse best = null; double bd = dist * dist;
        for (Entity e : p.getNearbyEntities(dist, dist, dist)) {
            if (e instanceof Horse h && h.getScoreboardTags().contains("offr_veh")) {
                double d = h.getLocation().distanceSquared(p.getLocation());
                if (d < bd) { bd = d; best = h; }
            }
        }
        return best;
    }

    private static NamespacedKey modelOf(ItemStack item) {
        if (item == null || !item.hasItemMeta()) return null;
        ItemMeta meta = item.getItemMeta();
        try {
            return meta.getItemModel();          // 1.21.2+: componenta item_model
        } catch (Throwable t) {
            return null;
        }
    }

    private int score(Entity e, String objective) {
        var obj = Bukkit.getScoreboardManager().getMainScoreboard().getObjective(objective);
        return obj == null ? 0 : obj.getScore(e.getUniqueId().toString()).getScore();
    }

    private void setScore(Entity e, String objective, int val) {
        var obj = Bukkit.getScoreboardManager().getMainScoreboard().getObjective(objective);
        if (obj != null) obj.getScore(e.getUniqueId().toString()).setScore(val);
    }

    private void play(Entity at, String sound, float volume, float pitch) {
        at.getWorld().playSound(at.getLocation(), sound, SoundCategory.MASTER, volume, pitch);
    }

    private static void actionbar(Player p, String text) {
        p.sendActionBar(net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer.legacySection().deserialize(text));
    }

    private void console(String cmd) {
        Bukkit.dispatchCommand(Bukkit.getConsoleSender(), cmd);
    }

    private static double clamp(double v, double min, double max) {
        return Math.max(min, Math.min(max, v));
    }
}
