package com.arena.offroader;

import org.bukkit.Bukkit;
import org.bukkit.entity.Horse;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.Vector;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * OffroaderPlugin — creierul mașinii: citește W/A/S/D direct din client
 * (Player#getCurrentInput) și conduce calul-vehicul ca în mod:
 *  - W = accelerează, S = frână/mers înapoi
 *  - A/D = viraj (camera rămâne LIBERĂ — mașina nu se întoarce după mouse!)
 *  - Spațiu = săritură off-road, Shift = frână de mână
 *  - Volanul (click-dreapta) pornește BOOST prin scorul offr.boost din datapack
 *  - Fără combustibil (offr.fuel) mașina nu mai prinde viteză
 * Șaua se scoate automat: clientul nu mai poate conduce singur calul,
 * singura autoritate este pluginul (fără luptă client/server).
 * Modelul, sunetele, HUD-ul și combustibilul rămân în datapack (cooperare).
 */
public final class OffroaderPlugin extends JavaPlugin {

    /** viteză pe tick, pe vehicul (bloc/tick) */
    private final Map<UUID, Double> speed = new HashMap<>();
    /** unghiul mașinii (grade), pe vehicul */
    private final Map<UUID, Float> carYaw = new HashMap<>();

    private static final double ACCEL = 0.022;     // accelerație normală (b/t²)
    private static final double ACCEL_BOOST = 0.046;
    private static final double MAX_SPEED = 0.42;  // ~30 km/h
    private static final double MAX_SPEED_BOOST = 0.62; // ~45 km/h
    private static final double MAX_REVERSE = 0.12;
    private static final double FRICTION = 0.91;
    private static final float TURN_RATE = 3.2f;   // grade/tick la viraj complet

    @Override
    public void onEnable() {
        getLogger().info("OffroaderPlugin activ — condus ca în mod (W/A/S/D, camera liberă).");
        Bukkit.getScheduler().runTaskTimer(this, this::tick, 1L, 1L);
    }

    private void tick() {
        boolean fuelBoard = Bukkit.getScoreboardManager().getMainScoreboard().getObjective("offr.fuel") != null;
        for (var world : Bukkit.getWorlds()) {
            for (Entity e : world.getEntities()) {
                if (!(e instanceof Horse horse)) continue;
                if (!horse.getScoreboardTags().contains("offr_veh")) continue;

                Player driver = null;
                for (Entity p : horse.getPassengers()) {
                    if (p instanceof Player pl) { driver = pl; break; }
                }
                if (driver == null) {
                    // fără șofer: starea se stinge singură
                    speed.remove(horse.getUniqueId());
                    continue;
                }

                // șaua jos — doar pluginul conduce (clientul nu poate conduce fără șa)
                if (horse.getInventory().hasSaddle()) {
                    horse.getInventory().setSaddle(false);
                }

                drive(horse, driver, fuelBoard);
            }
        }
    }

    /** citește un scor datapack al entității (cheia = UUID) */
    private int score(Entity e, String objective) {
        var obj = Bukkit.getScoreboardManager().getMainScoreboard().getObjective(objective);
        if (obj == null) return 0;
        return obj.getScore(e.getUniqueId().toString()).getScore();
    }

    private void drive(Horse horse, Player player, boolean fuelBoard) {
        var in = player.getCurrentInput();

        float steer = 0f;
        if (in.isLeft()) steer += 1f;
        if (in.isRight()) steer -= 1f;

        double throttle = 0;
        if (in.isForward()) throttle += 1;
        if (in.isBackward()) throttle -= 1;

        // fără combustibil → fără tracțiune (fricțiunea rămâne)
        int fuel = fuelBoard ? score(horse, "offr.fuel") : 1;
        if (fuel <= 0) throttle = Math.min(throttle, 0);

        // BOOST: setat de datapack la click-dreapta cu volanul (offr.boost, scade singur)
        boolean boost = score(horse, "offr.boost") > 0;

        UUID id = horse.getUniqueId();
        double v = speed.getOrDefault(id, 0.0);
        float yaw = carYaw.getOrDefault(id, horse.getLocation().getYaw());

        // accelerație + frecare
        double accel = boost ? ACCEL_BOOST : ACCEL;
        v += throttle * accel;
        v *= FRICTION;
        if (in.isSneak()) v = 0;                       // frână de mână (Shift)
        double max = boost ? MAX_SPEED_BOOST : MAX_SPEED;
        if (v > max) v = max;
        if (v < -MAX_REVERSE) v = -MAX_REVERSE;
        if (Math.abs(v) < 0.003 && throttle == 0) v = 0;

        // viraj: sensibil la viteză (la fel ca în mod)
        float speedFactor = (float) Math.min(1.0, 0.35 + Math.abs(v) / 0.25);
        yaw += steer * TURN_RATE * speedFactor * (v < 0 ? -1 : 1);
        yaw = (yaw % 360f + 360f) % 360f;

        // direcția de mers (yaw Bukkit: 0 = sud/+Z)
        double rad = Math.toRadians(yaw);
        Vector dir = new Vector(-Math.sin(rad), 0.0, Math.cos(rad));

        Vector vel = dir.multiply(v);
        vel.setY(horse.getVelocity().getY());          // gravitația rămâne a lui
        if (in.isJump() && horse.isOnGround()) vel.setY(0.52);

        horse.setRotation(yaw, 0f);
        horse.setVelocity(vel);

        speed.put(id, v);
        carYaw.put(id, yaw);
    }
}
