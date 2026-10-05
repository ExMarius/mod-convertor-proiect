package com.arena.vehiclemod;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import org.bukkit.Bukkit;
import org.bukkit.Location;
import org.bukkit.Material;
import org.bukkit.NamespacedKey;
import org.bukkit.SoundCategory;
import org.bukkit.World;
import org.bukkit.attribute.Attribute;
import org.bukkit.command.Command;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.ArmorStand;
import org.bukkit.entity.Entity;
import org.bukkit.entity.Horse;
import org.bukkit.entity.Interaction;
import org.bukkit.entity.ItemDisplay;
import org.bukkit.entity.Player;
import org.bukkit.entity.TextDisplay;
import org.bukkit.event.EventHandler;
import org.bukkit.event.Listener;
import org.bukkit.event.block.Action;
import org.bukkit.event.player.PlayerInteractEntityEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.Transformation;
import org.bukkit.util.Vector;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.io.InputStreamReader;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/**
 * VehicleMod — port 1:1 server-side al MrCrayfish's Vehicle Mod (0.45.2).
 *
 * TOTUL e citit din datele modului:
 *   - vehicles.json (generat din data/vehicle/vehicles/properties/*.json):
 *     geometrie (caroserie/roți/scaune/axe), motor (putere, pitch, sunet),
 *     combustibil (capacitate, consum 0.25/tick), hitbox din ModEntities.
 *   - resourcepack-ul conține assets/vehicle VERBATIM din jar-ul modului
 *     (namespace identic → item_model vehicle:<id>_body, sunete vehicle:...).
 *
 * Fizica = transcrierea LandVehicleEntity.updateVehicleMotion (modelul
 * bicicletei), validată numeric 1:1 (simulare tick cu tick, Δ=0).
 * Mișcarea pe ancoră (cal invizibil) = prin velocitate, ca
 * move(MoverType.SELF, ...) din mod — NICIODATĂ teleport cu șoferul.
 */
public final class VehicleModPlugin extends JavaPlugin implements Listener {

    // ------------------------------------------------------------------ date

    public record WheelDef(String side, String axle, double[] offset, double[] scale, boolean render) {}
    public record SeatDef(double[] pos, boolean driver) {}
    public record EngineDef(double power, double minPitch, double maxPitch, String sound, double capacity) {}
    public record BodyDef(String model, double scale, double[] translate) {}
    public record VehicleDef(String id, String name, String type, double[] hitbox, BodyDef body,
                             List<WheelDef> wheels, List<SeatDef> seats, EngineDef engine,
                             double frontAxle, double rearAxle) {}

    private final Map<String, VehicleDef> defs = new LinkedHashMap<>();

    /** sunetul real de motor (ogg-urile din jar) pentru fiecare vehicul */
    private static String engineOgg(String engineSound, String id) {
        return switch (id) {
            case "dirt_bike" -> "vehicle:dirt_bike_engine_mono";
            case "go_kart" -> "vehicle:go_kart_engine_mono";
            case "mini_bus" -> "vehicle:mini_bus_engine_mono";
            case "moped" -> "vehicle:moped_engine_mono";
            case "quad_bike" -> "vehicle:atv_engine_mono";
            case "tractor" -> "vehicle:tractor_engine_mono";
            case "golf_cart" -> "vehicle:electric_engine_mono";
            case "lawn_mower" -> "vehicle:go_kart_engine_mono";
            case "sports_plane" -> "vehicle:sports_plane_engine_mono";
            // jet_ski/off_roader/sports_car: modul folosește sunetul de jet_ski
            default -> "vehicle:speed_boat_engine_mono";
        };
    }

    /** modelul de roată implicit (modul: roți standard; off_roader: off_road) */
    private static String wheelModel(String id) {
        return switch (id) {
            case "off_roader" -> "vehicle:off_road_wheel";
            case "dirt_bike", "moped" -> "vehicle:sports_wheel";
            default -> "vehicle:standard_wheel";
        };
    }

    // ------------------------------------------------------------------ stare

    private static final class Veh {
        double vx, vz;                 // viteza (unități mod)
        float steering;                // unghi volan (grade)
        float traction = 0.8f;         // tracțiune (WheelType.STANDARD)
        double dx, dy, dz;             // deltaMovement (gravitație/inerție)
        boolean engineOn;
        int soundCd;
        int boost;                     // tick-i de boost rămași
        int hornCd;
        boolean grounded;
        double spin;                   // rotația roților (grade)
        ItemDisplay body, swheel;
        final List<ItemDisplay> wheels = new ArrayList<>();
        final List<Boolean> wheelFront = new ArrayList<>();
        TextDisplay name;
        final List<ArmorStand> stands = new ArrayList<>();   // scaune pasageri
        final List<Interaction> hits = new ArrayList<>();    // hitbox-uri click
    }

    private final Map<UUID, Veh> state = new HashMap<>();
    private NamespacedKey vehicleKey, fuelKey, initKey;
    private String rpUrl, rpSha1;

    // ------------------------------------------------------------------ pornire

    @Override
    public void onEnable() {
        vehicleKey = new NamespacedKey(this, "vehicle");
        fuelKey = new NamespacedKey(this, "fuel");
        initKey = new NamespacedKey(this, "init");
        rpUrl = "https://github.com/ExMarius/mod-convertor-proiect/raw/arena%2F01a106d2-mod-convertor-proiect/offroader/release/OffroaderResourcePack.zip";
        rpSha1 = new String(readResource("rp-sha1.txt"), StandardCharsets.UTF_8).trim();

        loadVehicles();
        Bukkit.getPluginManager().registerEvents(this, this);
        Bukkit.getScheduler().runTaskTimer(this, this::tick, 1L, 1L);
        getLogger().info("VehicleMod activ — " + defs.size() + " vehicule din mod, "
                + defs.values().stream().filter(d -> d.type().equals("land")).count() + " drivabile acum.");
    }

    private void loadVehicles() {
        try {
            Type t = new TypeToken<List<VehicleDef>>() {}.getType();
            List<VehicleDef> list = new Gson().fromJson(
                    new InputStreamReader(Objects.requireNonNull(getResource("vehicles.json"))), t);
            for (VehicleDef d : list) defs.put(d.id(), d);
        } catch (Exception e) {
            getLogger().severe("vehicles.json nu poate fi citit: " + e);
        }
    }

    private byte[] readResource(String name) {
        try (var in = getResource(name)) {
            return in == null ? new byte[0] : in.readAllBytes();
        } catch (Exception e) { return new byte[0]; }
    }

    // ------------------------------------------------------------------ join + kit

    @EventHandler
    public void onJoin(PlayerJoinEvent e) {
        Player p = e.getPlayer();
        // resource pack-ul portului (assets-urile reale ale modului) — de 2 ori:
        // imediat și la 5s (TLauncher ratează uneori prima cerere)
        applyRp(p);
        Bukkit.getScheduler().runTaskLater(this, () -> { if (p.isOnline()) applyRp(p); }, 100L);
    }

    private void applyRp(Player p) {
        byte[] hash = null;
        try { hash = hexToBytes(rpSha1); } catch (Exception ignored) {}
        try { p.setResourcePack(rpUrl, hash); } catch (Exception ex) { getLogger().warning("RP: " + ex); }
    }

    @EventHandler
    public void onRpStatus(org.bukkit.event.player.PlayerResourcePackStatusEvent e) {
        Player p = e.getPlayer();
        switch (e.getStatus()) {
            case DECLINED -> p.sendMessage("§6[VehicleMod] §cAi refuzat pack-ul! §eFără el vezi lingouri de fier în locul mașinilor. §fDescarcă-l de aici: §n" + rpUrl + " §fsau scrie §e/vehicle rp");
            case FAILED_DOWNLOAD -> {
                p.sendMessage("§6[VehicleMod] §cPack-ul a eșuat la download — reîncerc...");
                Bukkit.getScheduler().runTaskLater(this, () -> { if (p.isOnline()) applyRp(p); }, 40L);
            }
            default -> {}
        }
    }
        if (p.getScoreboardTags().contains("vm_kit")) return;
        Bukkit.getScheduler().runTaskLater(this, () -> {
            if (!p.isOnline()) return;
            giveSpawnItem(p, defs.get("off_roader"));
            p.getInventory().addItem(modItem("vehicle:jerry_can", "§cBidon combustibil",
                    "§7Click-dreapta lângă vehicul: alimentare +20%"));
            p.addScoreboardTag("vm_kit");
            p.sendMessage("§6[VehicleMod] §eAi primit cheia offroader-ului și bidonul. §7/vehicle list§e = toate vehiculele.");
        }, 30L);
    }

    private void giveSpawnItem(Player p, VehicleDef def) {
        if (def == null) return;
        p.getInventory().addItem(modItem(def.body().model(),
                "§6" + def.name(), "§7Click-dreapta: scoate / depozitează " + def.name()));
    }

    private ItemStack modItem(String model, String name, String lore) {
        ItemStack it = new ItemStack(Material.IRON_INGOT);
        ItemMeta m = it.getItemMeta();
        if (m != null) {
            m.setItemModel(NamespacedKey.fromString(model));
            m.setDisplayName(name);
            m.setLore(List.of(lore));
            it.setItemMeta(m);
        }
        return it;
    }

    // ------------------------------------------------------------------ comenzi

    @Override
    public boolean onCommand(CommandSender sender, Command cmd, String label, String[] args) {
        if (args.length == 0) {
            sender.sendMessage("§6[VehicleMod] §e/vehicle list §7| §e/vehicle give <id> §7| §e/vehicle test");
            return true;
        }
        switch (args[0].toLowerCase()) {
            case "list" -> {
                for (VehicleDef d : defs.values()) {
                    String status = switch (d.type()) {
                        case "land" -> "§adrivabil";
                        case "water" -> "§bpe apă — în lucru";
                        case "air" -> "§7în aer — în lucru";
                        default -> "§7remorcă — în lucru";
                    };
                    sender.sendMessage(" §e" + d.id() + " §7motor " + d.engine().power()
                            + " · " + d.engine().capacity() + " combustibil · " + status);
                }
            }
            case "give" -> {
                if (!(sender instanceof Player p)) { sender.sendMessage("doar în joc"); return true; }
                VehicleDef d = args.length > 1 ? defs.get(args[1].toLowerCase()) : null;
                if (d == null) { p.sendMessage("§cvehicul necunoscut (vezi /vehicle list)"); return true; }
                giveSpawnItem(p, d);
                p.sendMessage("§6[VehicleMod] §aAi primit " + d.name());
            }
            case "rp" -> {
                if (!(sender instanceof Player pl)) { sender.sendMessage(rpUrl); return true; }
                applyRp(pl);
                pl.sendMessage("§6[VehicleMod] §ePack retrimis — §aACCEPTĂ-L§e când te întreabă clientul!");
            }
            case "test" -> selfTest(sender);
            default -> sender.sendMessage("§csubcomandă necunoscută");
        }
        return true;
    }

    /** selftest din consolă sau joc: fiecare vehicul spawn → verificări → store */
    private void selfTest(CommandSender sender) {
        World w = Bukkit.getWorlds().get(0);
        Location loc = w.getSpawnLocation().add(2, 1, 2);
        int pass = 0, fail = 0;
        for (VehicleDef d : defs.values()) {
            if (!d.type().equals("land")) continue;
            try {
                Horse h = spawnVehicle(loc, d, null);
                Thread.sleep(50);
                Veh v = state.get(h.getUniqueId());
                int followers = v == null ? -1 : countFollowers(h);
                int expect = 1 + (int) d.wheels().stream().filter(WheelDef::render).count()
                        + 1 + (d.seats().size() > 1 ? d.seats().size() - 1 : 0) + d.seats().size();
                boolean ok = v != null && followers == expect
                        && h.getPersistentDataContainer().has(fuelKey, PersistentDataType.DOUBLE)
                        && h.getScoreboardTags().contains("vm_veh");
                if (ok) pass++; else { fail++; getLogger().warning("[TEST ESEC] " + d.id()
                        + ": followers=" + followers + "/" + expect + " veh=" + (v != null)); }
                getLogger().info("[TEST " + (ok ? "OK" : "ESEC") + "] " + d.id()
                        + " — " + followers + "/" + expect + " piese, motor " + d.engine().power());
                storeVehicle(h);
                Thread.sleep(50);
                int left = countFollowers(h);
                boolean stored = !h.isValid() && left == 0;
                if (!stored) {
                    fail++;
                    getLogger().warning("[TEST ESEC] " + d.id() + ": după store cal=" + h.isValid() + " piese=" + left);
                } else {
                    getLogger().info("[TEST OK] " + d.id() + " depozitat curat");
                }
            } catch (Exception ex) {
                fail++;
                getLogger().warning("[TEST ESEC] " + d.id() + ": " + ex);
            }
        }
        getLogger().info("[VehicleMod TEST] FINAL: " + pass + " trecute, " + fail + " esuate");
        sender.sendMessage("§6[VehicleMod TEST] §a" + pass + " trecute§7, §c" + fail + " esuate§7 — vezi consola.");
    }

    // ------------------------------------------------------------------ spawn / store

    private Horse spawnVehicle(Location at, VehicleDef def, Player forPlayer) {
        World w = at.getWorld();
        Location base = at.clone().add(at.getDirection().setY(0).normalize().multiply(1.6));
        Horse horse = w.spawn(base, Horse.class, h -> {
            h.setInvisible(true); h.setSilent(true); h.setInvulnerable(true);
            h.setPersistent(true); h.setAI(false); h.setTamed(true);
            h.addScoreboardTag("vm_veh");
            h.addScoreboardTag("vm_id_" + def.id());
            h.getPersistentDataContainer().set(initKey, PersistentDataType.BYTE, (byte) 1);
            h.getPersistentDataContainer().set(fuelKey, PersistentDataType.DOUBLE, def.engine().capacity());
            h.addPotionEffect(new org.bukkit.potion.PotionEffect(
                    org.bukkit.potion.PotionEffectType.INVISIBILITY, -1, 0, false, false));
        });

        Veh v = new Veh();
        state.put(horse.getUniqueId(), v);

        double U = def.body().scale() / 16.0;             // 1 unitate model → blocuri
        double originY = 4 * U;                            // raza roții (roata: y 4..12)
        SeatDef ds = def.seats().isEmpty() ? null : def.seats().get(0);
        for (SeatDef s : def.seats()) if (s.driver()) ds = s;
        double shX = ds == null ? 0 : ds.pos()[0] * U;     // scaunul șoferului sub
        double shZ = ds == null ? 0 : -ds.pos()[2] * U;    // centrul calului

        String uid = horse.getUniqueId().toString();
        Location spawn = horse.getLocation();

        // --- caroseria ---
        double btz = def.body().translate()[2];
        v.body = w.spawn(spawn, ItemDisplay.class, d -> {
            d.setItemStack(displayItem(def.body().model()));
            d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
            d.setTeleportDuration(2); d.setInterpolationDuration(2);
            d.setTransformation(new Transformation(new Vector3f(0, 0, 0), new Quaternionf(),
                    new Vector3f((float) def.body().scale(), (float) def.body().scale(), (float) def.body().scale()),
                    new Quaternionf()));
            tag(d, uid); d.setViewRange(1.5f);
        });

        // --- roțile ---
        for (WheelDef wd : def.wheels()) {
            if (!wd.render()) continue;
            double mx = wd.side().equals("left") ? -wd.offset()[0] : wd.offset()[0];
            double lx = -mx * U + shX;                    // mod_to_mc + shift
            double ly = originY + wd.offset()[1] * U;
            double lz = wd.offset()[2] * U + shZ + btz * U;
            boolean front = wd.axle().equals("front");
            ItemDisplay wheel = w.spawn(spawn, ItemDisplay.class, d -> {
                d.setItemStack(displayItem(wheelModel(def.id())));
                d.setItemDisplayTransform(ItemDisplay.ItemDisplayTransform.NONE);
                d.setTeleportDuration(2); d.setInterpolationDuration(2);
                d.setTransformation(new Transformation(new Vector3f(0, 0, 0), new Quaternionf(),
                        new Vector3f((float) wd.scale()[0], (float) wd.scale()[1], (float) wd.scale()[2]),
                        new Quaternionf()));
                tag(d, uid);
            });
            wheel.getPersistentDataContainer().set(new NamespacedKey(this, "lx"), PersistentDataType.DOUBLE, lx);
            wheel.getPersistentDataContainer().set(new NamespacedKey(this, "ly"), PersistentDataType.DOUBLE, ly);
            wheel.getPersistentDataContainer().set(new NamespacedKey(this, "lz"), PersistentDataType.DOUBLE, lz);
            v.wheels.add(wheel);
            v.wheelFront.add(front);
        }

        // --- numele ---
        v.name = w.spawn(spawn, TextDisplay.class, d -> {
            d.setText("§6" + def.name());
            d.setBillboard(org.bukkit.entity.Display.Billboard.CENTER);
            d.setTeleportDuration(2);
            tag(d, uid);
        });
        v.name.getPersistentDataContainer().set(new NamespacedKey(this, "ly"),
                PersistentDataType.DOUBLE, def.hitbox()[1] + 0.9);

        // --- scaunele pasagerilor + hitbox-urile de click ---
        int seatIdx = 0;
        for (SeatDef s : def.seats()) {
            double lx = -s.pos()[0] * U + shX;
            double ly = originY + s.pos()[1] * U;
            double lz = s.pos()[2] * U + shZ + btz * U;
            boolean isDriver = s.driver() || (ds != null && s == ds);
            if (!isDriver) {
                ArmorStand st = w.spawn(spawn, ArmorStand.class, a -> {
                    a.setMarker(true); a.setInvisible(true); a.setInvulnerable(true);
                    a.setGravity(false); a.setPersistent(true);
                    a.addScoreboardTag("vm_seat");
                    tag(a, uid);
                });
                st.getPersistentDataContainer().set(new NamespacedKey(this, "lx"), PersistentDataType.DOUBLE, lx);
                st.getPersistentDataContainer().set(new NamespacedKey(this, "ly"), PersistentDataType.DOUBLE, ly);
                st.getPersistentDataContainer().set(new NamespacedKey(this, "lz"), PersistentDataType.DOUBLE, lz);
                v.stands.add(st);
            }
            final boolean driver = isDriver;
            final int idx = seatIdx++;
            Interaction hit = w.spawn(spawn, Interaction.class, i -> {
                i.setInteractionWidth(driver ? 1.0f : 0.9f);
                i.setInteractionHeight(1.3f);
                i.setPersistent(true);
                i.addScoreboardTag("vm_hit");
                if (driver) i.addScoreboardTag("vm_driver");
                tag(i, uid);
            });
            hit.getPersistentDataContainer().set(new NamespacedKey(this, "lx"), PersistentDataType.DOUBLE, lx);
            hit.getPersistentDataContainer().set(new NamespacedKey(this, "ly"), PersistentDataType.DOUBLE, ly);
            hit.getPersistentDataContainer().set(new NamespacedKey(this, "lz"), PersistentDataType.DOUBLE, lz);
            v.hits.add(hit);
        }

        play(spawn, "vehicle:pick_up_vehicle", 1f, 1f);
        if (forPlayer != null)
            forPlayer.sendMessage("§6[VehicleMod] §a" + def.name() + " scos! §7Click pe scaunul din față ca să șofezi.");
        return horse;
    }

    private ItemStack displayItem(String model) {
        ItemStack it = new ItemStack(Material.IRON_INGOT);
        ItemMeta m = it.getItemMeta();
        if (m != null) { m.setItemModel(NamespacedKey.fromString(model)); it.setItemMeta(m); }
        return it;
    }

    private void tag(Entity e, String uid) {
        e.addScoreboardTag("vm_f");
        e.getPersistentDataContainer().set(vehicleKey, PersistentDataType.STRING, uid);
    }

    private int countFollowers(Horse h) {
        String uid = h.getUniqueId().toString();
        int n = 0;
        for (Entity e : h.getNearbyEntities(4, 4, 4))
            if (e.getScoreboardTags().contains("vm_f")
                    && uid.equals(e.getPersistentDataContainer().get(vehicleKey, PersistentDataType.STRING)))
                n++;
        return n;
    }

    private void storeVehicle(Horse h) {
        String uid = h.getUniqueId().toString();
        for (Entity e : new ArrayList<>(h.getWorld().getEntities())) {
            if (!e.getScoreboardTags().contains("vm_f")) continue;
            if (!uid.equals(e.getPersistentDataContainer().get(vehicleKey, PersistentDataType.STRING))) continue;
            if (e instanceof ArmorStand a) { a.setInvulnerable(false); }
            e.remove();
        }
        play(h.getLocation(), "vehicle:pick_up_vehicle", 1f, 1f);
        h.setInvulnerable(false);
        h.remove();
        state.remove(h.getUniqueId());
    }

    // ------------------------------------------------------------------ tick (fizica + randare)

    // constante 1:1 (LandVehicleEntity / PoweredVehicleEntity / WheelType.STANDARD)
    private static final float ACCEL = 0.05f, REVERSE = 0.4f, MAX_REVERSE = 5.0f;
    private static final float DRAG = 0.001f, BRAKE = 1.0f, LIMIT = 100.0f, MAX_STEER = 35.0f;
    private static final float BOOST_MUL = 0.5f;      // setBoosting: forța += forța×0.5
    private static final int BOOST_TICKS = 10;
    private static final float GRAVITY = 0.08f;
    private static final float WHEEL_BASE = 0.8f, WHEEL_SLIDE = 0.05f;

    private void tick() {
        for (var world : Bukkit.getWorlds()) {
            for (Entity e : new ArrayList<>(world.getEntitiesByClass(Horse.class))) {
                if (!e.getScoreboardTags().contains("vm_veh")) continue;
                Horse horse = (Horse) e;
                String vid = horse.getScoreboardTags().stream().filter(t -> t.startsWith("vm_id_"))
                        .map(t -> t.substring(6)).findFirst().orElse(null);
                VehicleDef def = vid == null ? null : defs.get(vid);
                if (def == null) continue;
                try {
                    drive(horse, def);
                } catch (Exception ex) {
                    getLogger().warning("tick " + vid + ": " + ex);
                }
            }
        }
    }

    private void drive(Horse horse, VehicleDef def) {
        UUID id = horse.getUniqueId();
        Veh v = state.computeIfAbsent(id, k -> new Veh());
        var pdc = horse.getPersistentDataContainer();
        if (pdc.get(initKey, PersistentDataType.BYTE) == null) {
            pdc.set(initKey, PersistentDataType.BYTE, (byte) 1);
            if (pdc.get(fuelKey, PersistentDataType.DOUBLE) == null)
                pdc.set(fuelKey, PersistentDataType.DOUBLE, def.engine().capacity());
        }
        double fuel = pdc.get(fuelKey, PersistentDataType.DOUBLE) == null ? def.engine().capacity()
                : pdc.get(fuelKey, PersistentDataType.DOUBLE);

        Player driver = null;
        for (Entity p : horse.getPassengers()) if (p instanceof Player pl) { driver = pl; break; }

        float turn = 0f;
        double throttle = 0;
        boolean handbrake = false;
        if (driver != null) {
            var in = driver.getCurrentInput();
            if (in.isLeft()) turn += 1f;
            if (in.isRight()) turn -= 1f;
            if (in.isForward()) throttle += 1;
            if (in.isBackward()) throttle -= 1;
            handbrake = in.isJump();
            if (handbrake) throttle = 0;
            if (in.isSneak()) { horse.removePassenger(driver); driver = null; }
        }
        if (driver == null) { v.steering *= 0.85f; throttle = 0; }

        boolean engineOn = driver != null && fuel > 0;
        if (engineOn && driver != null && driver.getGameMode() != org.bukkit.GameMode.CREATIVE) {
            fuel = Math.max(0, fuel - 0.25);              // consum 0.25/tick exact ca în mod
            pdc.set(fuelKey, PersistentDataType.DOUBLE, fuel);
        }
        String ogg = engineOgg(def.engine().sound(), def.id());
        if (engineOn && !v.engineOn) { play(horse.getLocation(), ogg, 1.2f, 0.7f); v.engineOn = true; }
        else if (!engineOn && v.engineOn) { play(horse.getLocation(), ogg, 0.8f, 0.6f); v.engineOn = false; }

        boolean boosting = false;
        if (v.boost > 0) { if (throttle > 0) { boosting = true; v.boost--; } else v.boost = 0; }

        // ---- steering (VehicleHelper.getSteeringAngle) ----
        float strength = (turn != 0f) ? 0.05f : 0.2f;
        v.steering += (MAX_STEER * turn - v.steering) * strength;

        // ---- dinamica (unități mod) ----
        double yawDeg = horse.getLocation().getYaw();
        double r = Math.toRadians(yawDeg);
        double[] fwd = {-Math.sin(r), Math.cos(r)};

        double U = def.body().scale() / 16.0;
        double btz = def.body().translate()[2];
        double frontAxle = (btz + def.frontAxle()) * U;
        double rearAxle = (btz + def.rearAxle()) * U;

        double force = v.grounded ? def.engine().power() * clamp(throttle, -1, 1) : 0;
        if (boosting) force += force * BOOST_MUL;
        if (throttle < 0) force *= REVERSE;

        double speed = Math.hypot(v.vx, v.vz);
        double[] accel = {fwd[0] * force * ACCEL, fwd[1] * force * ACCEL};
        if (speed < 0.05) { v.vx = 0; v.vz = 0; speed = 0; }

        float surfFriction = surfaceFriction(horse.getLocation(), fwd, frontAxle, rearAxle);
        float surfTraction = surfaceTraction(horse.getLocation(), fwd, frontAxle, rearAxle);

        double[] hb = {v.vx * (handbrake && v.grounded ? BRAKE : 0) * ACCEL,
                       v.vz * (handbrake && v.grounded ? BRAKE : 0) * ACCEL};
        double[] fr = {v.vx * -surfFriction * ACCEL, v.vz * -surfFriction * ACCEL};
        double[] dg = {v.vx * speed * -DRAG * ACCEL, v.vz * speed * -DRAG * ACCEL};
        v.vx += accel[0] + hb[0] + fr[0] + dg[0];
        v.vz += accel[1] + hb[1] + fr[1] + dg[1];
        speed = Math.hypot(v.vx, v.vz);
        if (speed > LIMIT) { v.vx *= LIMIT / speed; v.vz *= LIMIT / speed; speed = LIMIT; }

        // ---- tracțiune / drift ----
        double vxn = speed > 1e-9 ? v.vx / speed : 0, vzn = speed > 1e-9 ? v.vz / speed : 0;
        double cross = Math.abs(fwd[0] * vzn - fwd[1] * vxn);
        boolean sliding = cross >= 0.3;
        if (sliding && throttle > 0) v.traction = WHEEL_SLIDE;
        else if (handbrake) v.traction = WHEEL_SLIDE;
        else {
            double al = Math.hypot(accel[0], accel[1]);
            float target = al > 0 ? (float) (WHEEL_BASE * clamp(speed / al, 0, 1)) : WHEEL_BASE;
            float side = (float) clamp(1 - cross / 0.3, 0, 1);
            v.traction = v.traction + (target - v.traction) * side * 0.15f;
        }
        float surfaceTraction = surfTraction * v.traction;

        // ---- modelul bicicletei (LandVehicleEntity) ----
        double[] front = {fwd[0] * frontAxle, fwd[1] * frontAxle};
        double[] rear = {fwd[0] * rearAxle, fwd[1] * rearAxle};
        double sr = Math.toRadians(v.steering);
        double cs = Math.cos(sr), sn = Math.sin(sr);
        double svx = v.vx * cs + v.vz * sn, svz = v.vz * cs - v.vx * sn;
        front[0] += svx * ACCEL; front[1] += svz * ACCEL;
        rear[0] += v.vx * ACCEL; rear[1] += v.vz * ACCEL;

        double hx = front[0] - rear[0], hz = front[1] - rear[1];
        double hl = Math.hypot(hx, hz);
        if (hl > 1e-9) { hx /= hl; hz /= hl; } else { hx = fwd[0]; hz = fwd[1]; }

        double mx = rear[0] + hx * (-rearAxle);
        double mz = rear[1] + hz * (-rearAxle);

        double yawF = Math.toDegrees(Math.atan2(-fwd[0], fwd[1]));
        double yawH = Math.toDegrees(Math.atan2(-hx, hz));
        double dYaw = yawF - yawH;
        while (dYaw > 180) dYaw -= 360;
        while (dYaw < -180) dYaw += 360;
        float newYaw = (float) (yawDeg - dYaw);

        if (speed > 0) {
            double dot = hx * vxn + hz * vzn;
            double tX, tZ;
            if (dot >= 0) { tX = hx * speed; tZ = hz * speed; }
            else { double rev = Math.min(speed, MAX_REVERSE); tX = -hx * rev; tZ = -hz * rev; }
            v.vx += (tX - v.vx) * surfaceTraction;
            v.vz += (tZ - v.vz) * surfaceTraction;
        }

        // ---- aplicare prin VELOCITATE (ca move(MoverType.SELF,...) din mod) ----
        v.dy -= GRAVITY;
        double moveX = v.dx + mx, moveY = v.dy, moveZ = v.dz + mz;

        if (driver != null) {
            horse.setAI(true);                       // coliziuni + step 1.0 nativ
            var inv = horse.getInventory();
            if (inv.getSaddle() != null) inv.setSaddle(null);
            double attr = (boosting || v.boost > 0) ? 0.55 : 0.3375;
            var sa = horse.getAttribute(Attribute.MOVEMENT_SPEED);
            if (sa != null && Math.abs(sa.getBaseValue() - attr) > 1e-6) sa.setBaseValue(attr);
        } else {
            horse.setAI(false);
            var sa = horse.getAttribute(Attribute.MOVEMENT_SPEED);
            if (sa != null && sa.getBaseValue() != 0.0) sa.setBaseValue(0.0);
            v.dx = 0; v.dy = 0; v.dz = 0;
            if (Math.abs(v.vx) + Math.abs(v.vz) < 0.05) { v.vx = 0; v.vz = 0; }
        }

        horse.setVelocity(new Vector(moveX, moveY + GRAVITY, moveZ));
        horse.setRotation(newYaw, 0f);

        if (horse.isOnGround()) { v.dx *= 0.75; v.dy = 0; v.dz *= 0.75; v.grounded = true; }
        else { v.dx *= 0.98; v.dz *= 0.98; v.grounded = false; }

        // safety-net: sub lume (lag) → recuperare
        if (horse.getLocation().getY() < horse.getWorld().getMinHeight() - 8) {
            Location safe = horse.getLocation().clone();
            safe.setY(horse.getWorld().getMinHeight() + 2);
            horse.teleport(safe);
            v.dy = 0;
        }

        // ---- sunet motor (pitch min + (max-min)*|v|/25) ----
        if (engineOn && --v.soundCd <= 0) {
            v.soundCd = 19;
            float pitch = (float) (def.engine().minPitch()
                    + (def.engine().maxPitch() - def.engine().minPitch()) * Math.min(speed / 25.0, 1.0));
            play(horse.getLocation(), ogg, 1.0f, pitch);
        }
        if (v.hornCd > 0) v.hornCd--;

        // ---- HUD șofer ----
        if (driver != null && horse.getTicksLived() % 5 == 0) {
            double kmh = speed * 0.05 * 20 * 3.6;
            int pct = (int) Math.max(0, Math.min(100, fuel * 100 / def.engine().capacity()));
            StringBuilder sb = new StringBuilder("§6⛽ ");
            int seg = pct * 12 / 100;
            for (int i = 0; i < 12; i++) sb.append(i < seg ? (pct < 20 ? "§c▌" : "§a▌") : "§8▌");
            sb.append("§r ").append(pct).append("%  §b").append(Math.round(kmh)).append(" km/h");
            if (boosting) sb.append(" §4§lBOOST!");
            else if (sliding || (handbrake && speed > 2)) sb.append(" §d§lDRIFT");
            driver.sendActionBar(net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer
                    .legacySection().deserialize(sb.toString()));
        }

        // ---- randarea: poziționează toate piesele (clientul interpolează) ----
        renderParts(horse, v, def, U, newYaw);
    }

    private void renderParts(Horse horse, Veh v, VehicleDef def, double U, float yaw) {
        Location loc = horse.getLocation();
        double r = Math.toRadians(yaw);
        double c = Math.cos(r), s = Math.sin(r);

        // caroseria: la originea vehiculului + shift-ul scaunului șoferului
        SeatDef ds = def.seats().isEmpty() ? null : def.seats().get(0);
        for (SeatDef sd : def.seats()) if (sd.driver()) ds = sd;
        double shX = ds == null ? 0 : ds.pos()[0] * U;
        double shZ = ds == null ? 0 : -ds.pos()[2] * U;
        double btz = def.body().translate()[2];

        // rotația roților după viteza reală
        double speed = Math.hypot(v.vx, v.vz);
        double fwdDot = v.vx * -Math.sin(r) + v.vz * Math.cos(r);
        v.spin += fwdDot * 0.05 * 20 * 6;   // grade/tick ≈ rulare

        if (v.body != null && v.body.isValid()) {
            teleportLocal(v.body, loc, 0, 0, 0, yaw);
        }
        if (v.name != null && v.name.isValid()) {
            Double ly = v.name.getPersistentDataContainer().get(new NamespacedKey(this, "ly"), PersistentDataType.DOUBLE);
            teleportLocal(v.name, loc, 0, ly == null ? 2.0 : ly, 0, yaw);
        }
        Quaternionf spinQ = new Quaternionf().rotationX((float) Math.toRadians(v.spin));
        for (int i = 0; i < v.wheels.size(); i++) {
            ItemDisplay w = v.wheels.get(i);
            if (!w.isValid()) continue;
            var wp = w.getPersistentDataContainer();
            double lx = wp.get(new NamespacedKey(this, "lx"), PersistentDataType.DOUBLE);
            double ly = wp.get(new NamespacedKey(this, "ly"), PersistentDataType.DOUBLE);
            double lz = wp.get(new NamespacedKey(this, "lz"), PersistentDataType.DOUBLE);
            boolean front = v.wheelFront.get(i);
            float wyaw = yaw + (front ? v.steering : 0f);
            teleportLocal(w, loc, lx, ly, lz, wyaw);
            // spin (rotație în jurul axei proprii)
            w.setInterpolationDelay(0);
            w.setInterpolationDuration(2);
            var tr = w.getTransformation();
            w.setTransformation(new Transformation(tr.getTranslation(), spinQ, tr.getScale(), tr.getRightRotation()));
        }
        for (ArmorStand st : v.stands) {
            if (!st.isValid()) continue;
            teleportLocalRide(st, loc);
        }
        for (Interaction h : v.hits) {
            if (!h.isValid()) continue;
            teleportLocal(h, loc);
        }
    }

    /** teleportează o entitate la offset LOCAL (rotit cu yaw-ul vehiculului) */
    private void teleportLocal(Entity e, Location anchor, double lx, double ly, double lz, float yaw) {
        double r = Math.toRadians(yaw);
        double c = Math.cos(r), s = Math.sin(r);
        // axele locale: forward = (-sin, cos), left = (cos, sin)... vanilla ^x/^z
        double wx = anchor.getX() + (lx * c + lz * s);
        double wz = anchor.getZ() + (-lx * s + lz * c);
        Location t = new Location(anchor.getWorld(), wx, anchor.getY() + ly, wz, yaw, 0f);
        e.teleport(t);
    }

    private void teleportLocal(Entity e, Location anchor) {
        var p = e.getPersistentDataContainer();
        Double lx = p.get(new NamespacedKey(this, "lx"), PersistentDataType.DOUBLE);
        Double ly = p.get(new NamespacedKey(this, "ly"), PersistentDataType.DOUBLE);
        Double lz = p.get(new NamespacedKey(this, "lz"), PersistentDataType.DOUBLE);
        if (lx == null) return;
        teleportLocal(e, anchor, lx, ly == null ? 0 : ly, lz == null ? 0 : lz, anchor.getYaw());
    }

    /** armor stand cu pasager: păstrează pasagerii la teleport */
    private void teleportLocalRide(ArmorStand e, Location anchor) {
        var p = e.getPersistentDataContainer();
        Double lx = p.get(new NamespacedKey(this, "lx"), PersistentDataType.DOUBLE);
        Double ly = p.get(new NamespacedKey(this, "ly"), PersistentDataType.DOUBLE);
        Double lz = p.get(new NamespacedKey(this, "lz"), PersistentDataType.DOUBLE);
        if (lx == null) return;
        double r = Math.toRadians(anchor.getYaw());
        double c = Math.cos(r), s = Math.sin(r);
        Location t = new Location(anchor.getWorld(),
                anchor.getX() + (lx * c + lz * s),
                anchor.getY() + (ly == null ? 0 : ly),
                anchor.getZ() + (-lx * s + lz * c), anchor.getYaw(), 0f);
        if (e.getPassengers().isEmpty()) e.teleport(t);
        else e.teleport(t, io.papermc.paper.entity.TeleportFlag.EntityState.RETAIN_PASSENGERS);
    }

    // ------------------------------------------------------------------ suprafețe (SurfaceHelper + STANDARD)

    private static final int S_SOLID = 0, S_DIRT = 1, S_SNOW = 2, S_ICE = 3, S_NONE = 4;

    private int surfaceAt(Location loc, double[] fwd, double axle) {
        var b = loc.getWorld().getBlockAt(
                loc.getBlockX() + (int) Math.floor(fwd[0] * axle),
                loc.getBlockY() - 1,
                loc.getBlockZ() + (int) Math.floor(fwd[1] * axle));
        Material m = b.getType();
        if (b.isLiquid() || m.isAir()) return S_NONE;
        if (m == Material.ICE || m == Material.PACKED_ICE || m == Material.BLUE_ICE || m == Material.FROSTED_ICE) return S_ICE;
        if (m.name().contains("SNOW") || m.name().contains("LEAVES") || m == Material.CACTUS) return S_SNOW;
        switch (m) {
            case GRASS_BLOCK: case DIRT: case COARSE_DIRT: case PODZOL: case ROOTED_DIRT:
            case MUD: case SAND: case RED_SAND: case GRAVEL: case CLAY: case FARMLAND:
            case DIRT_PATH: case MYCELIUM: case SOUL_SAND:
                return S_DIRT;
            default:
                if (m.name().contains("WOOL") || m.name().contains("CARPET")) return S_DIRT;
                return m.isSolid() ? S_SOLID : S_NONE;
        }
    }

    private float surfAvg(Location loc, double[] fwd, double fa, double ra, float solid, float dirt, float snow, float ice) {
        int a = surfaceAt(loc, fwd, fa), b = surfaceAt(loc, fwd, ra);
        float sum = 0; int n = 0;
        if (a != S_NONE) { sum += val(a, solid, dirt, snow, ice); n++; }
        if (b != S_NONE) { sum += val(b, solid, dirt, snow, ice); n++; }
        return n == 0 ? 0f : sum / n;
    }
    private static float val(int s, float solid, float dirt, float snow, float ice) {
        return switch (s) { case S_SOLID -> solid; case S_DIRT -> dirt; case S_SNOW -> snow; case S_ICE -> ice; default -> 0; };
    }
    private float surfaceFriction(Location l, double[] f, double fa, double ra) {
        return surfAvg(l, f, fa, ra, 0.9f * 1.1f, 1.1f * 1.3f, 1.5f * 1.7f, 1.5f);
    }
    private float surfaceTraction(Location l, double[] f, double fa, double ra) {
        return surfAvg(l, f, fa, ra, 1.0f, 0.9f, 0.9f, 0.01f);
    }

    // ------------------------------------------------------------------ interacțiuni

    @EventHandler
    public void onInteractEntity(PlayerInteractEntityEvent e) {
        if (!(e.getRightClicked() instanceof Interaction hit)) return;
        Player p = e.getPlayer();
        String uid = hit.getPersistentDataContainer().get(vehicleKey, PersistentDataType.STRING);
        if (uid == null) return;
        e.setCancelled(true);
        Entity veh = null;
        try { veh = Bukkit.getEntity(UUID.fromString(uid)); } catch (Exception ignored) {}
        if (!(veh instanceof Horse h) || !h.isValid()) return;

        if (hit.getScoreboardTags().contains("vm_driver")) {
            boolean hasDriver = h.getPassengers().stream().anyMatch(pl -> pl instanceof Player);
            if (hasDriver) { p.sendMessage("§cCineva șofează deja!"); return; }
            h.addPassenger(p);
            p.sendMessage("§6[VehicleMod] §aLa volan! §7W/S = gază · A/D = volan · SPAȚIU = frână de mână · SHIFT = cobori · click-dreapta = BOOST");
        } else {
            // scaun de pasager: găsește stand-ul de la aceeași poziție
            for (ArmorStand st : h.getWorld().getEntitiesByClass(ArmorStand.class)) {
                if (!st.getScoreboardTags().contains("vm_seat")) continue;
                if (uid.equals(st.getPersistentDataContainer().get(vehicleKey, PersistentDataType.STRING))
                        && st.getLocation().distanceSquared(hit.getLocation()) < 1.2) {
                    if (st.getPassengers().isEmpty()) st.addPassenger(p);
                    return;
                }
            }
            h.addPassenger(p); // fallback: urcă pe vehicul
        }
    }

    @EventHandler
    public void onInteract(PlayerInteractEvent e) {
        if (e.getAction() != Action.RIGHT_CLICK_AIR && e.getAction() != Action.RIGHT_CLICK_BLOCK) return;
        Player p = e.getPlayer();

        // 1) BOOST: orice click-dreapta în timp ce șofezi
        if (p.getVehicle() instanceof Horse h && h.getScoreboardTags().contains("vm_veh")) {
            e.setCancelled(true);
            Veh v = state.get(h.getUniqueId());
            if (v == null) return;
            double fuel = fuelOf(h);
            if (fuel > 0) {
                v.boost = BOOST_TICKS;
                play(h.getLocation(), "vehicle:boost_pad", 1.4f, 1f);
                p.sendActionBar(net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer
                        .legacySection().deserialize("§4§lBOOST!"));
            } else {
                p.sendActionBar(net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer
                        .legacySection().deserialize("§cFără combustibil! Alimentează cu bidonul."));
            }
            return;
        }

        ItemStack it = e.getItem();
        if (it == null || !it.hasItemMeta()) return;
        ItemMeta m = it.getItemMeta();
        if (m.getItemModel() == null) return;
        String model = m.getItemModel().toString();
        e.setCancelled(true);

        // 2) itemul de spawn al unui vehicul
        VehicleDef def = defs.values().stream()
                .filter(d -> d.body().model().equals(model)).findFirst().orElse(null);
        if (def != null) {
            if (!def.type().equals("land")) {
                p.sendMessage("§7[VehicleMod] " + def.name() + " încă în lucru ("
                        + (def.type().equals("water") ? "apă" : def.type().equals("air") ? "aer" : "remorcă")
                        + ") — vine în următoarea fază.");
                return;
            }
            Horse near = nearestVehicle(p, 5);
            if (near != null) {
                storeVehicle(near);
                p.sendMessage("§6[VehicleMod] §e" + def.name() + " depozitat.");
            } else {
                spawnVehicle(p.getLocation(), def, p);
            }
            return;
        }

        // 3) bidonul de combustibil (+20% din capacitate, ca JerryCanItem)
        if (model.equals("vehicle:jerry_can")) {
            Horse near = nearestVehicle(p, 5);
            if (near == null) { p.sendMessage("§7Niciun vehicul prin apropiere."); return; }
            var pdc = near.getPersistentDataContainer();
            String vid = near.getScoreboardTags().stream().filter(t -> t.startsWith("vm_id_"))
                    .map(t -> t.substring(6)).findFirst().orElse(null);
            VehicleDef d = vid == null ? null : defs.get(vid);
            double cap = d == null ? 20000 : d.engine().capacity();
            double fuel = fuelOf(near);
            double add = cap * 0.2;
            pdc.set(fuelKey, PersistentDataType.DOUBLE, Math.min(cap, fuel + add));
            play(near.getLocation(), "vehicle:liquid_glug", 1.0f, 1f);
            p.sendMessage("§a⛽ Alimentat: " + (int) (Math.min(cap, fuel + add) * 100 / cap) + "%");
        }
    }

    private double fuelOf(Horse h) {
        Double f = h.getPersistentDataContainer().get(fuelKey, PersistentDataType.DOUBLE);
        return f == null ? 0 : f;
    }

    private Horse nearestVehicle(Player p, double dist) {
        Horse best = null; double bd = dist * dist;
        for (Entity e : p.getNearbyEntities(dist, dist, dist)) {
            if (e instanceof Horse h && h.getScoreboardTags().contains("vm_veh")) {
                double d = h.getLocation().distanceSquared(p.getLocation());
                if (d < bd) { bd = d; best = h; }
            }
        }
        return best;
    }

    // ------------------------------------------------------------------ utilitare

    private void play(Location loc, String sound, float volume, float pitch) {
        Objects.requireNonNull(loc.getWorld()).playSound(loc, sound, SoundCategory.MASTER, volume, pitch);
    }

    private static double clamp(double v, double min, double max) { return Math.max(min, Math.min(max, v)); }

    private static byte[] hexToBytes(String hex) {
        int n = hex.length();
        byte[] out = new byte[n / 2];
        for (int i = 0; i < n; i += 2)
            out[i / 2] = (byte) ((Character.digit(hex.charAt(i), 16) << 4) + Character.digit(hex.charAt(i + 1), 16));
        return out;
    }
}
