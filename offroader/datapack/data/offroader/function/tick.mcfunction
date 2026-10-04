# heartbeat — contorizează că bucla tick e vie (folosit de selftest)
scoreboard players add #hb offr.dummy 1
# Bucla principală (20/s). Țintă: 1.21.4.
# Ordinea e defensivă: întâi acțiunile jucătorilor și vehiculele (critice),
# resigilarea NBT ultima (orice problemă acolo nu oprește restul).

# --- click-dreapta cu itemele custom (verificăm și modelul din mână) ---
execute as @a[scores={offr.key=1..}] at @s if items entity @s weapon.mainhand minecraft:warped_fungus_on_a_stick[item_model="offroader:key"] run function offroader:item_use/key
execute as @a[scores={offr.throttle=1..}] at @s if items entity @s weapon.mainhand minecraft:carrot_on_a_stick[item_model="offroader:steering_wheel"] run function offroader:item_use/throttle
execute as @a[scores={offr.can=1..}] at @s if items entity @s weapon.mainhand minecraft:fishing_rod[item_model="offroader:jerrycan"] run function offroader:item_use/jerrycan

# consumă trigger-ele rămase (inclusiv iteme vanilla cu același tip)
scoreboard players set @a[scores={offr.key=1..}] offr.key 0
scoreboard players set @a[scores={offr.throttle=1..}] offr.throttle 0
scoreboard players set @a[scores={offr.can=1..}] offr.can 0

# --- bucla vehiculelor (urmărirea mașinii, sunete, HUD) ---
execute as @e[type=minecraft:horse,tag=offr_veh] at @s run function offroader:veh/tick

# --- motor distrus -> reconstruit automat din caroserie ---
execute as @e[tag=offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] run function offroader:veh/revive

# --- piese cu adevărat orfane (fără cal ȘI fără caroserie) -> curățate ---
execute as @e[tag=offr_f,tag=!offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] unless entity @e[tag=offr_body,distance=..10] run kill @s

# --- resigilare NBT cal (ultima, defensiv) ---
data merge entity @e[type=minecraft:horse,tag=offr_veh] {Invulnerable:1b,Invisible:1b,Silent:1b,PersistenceRequired:1b,active_effects:[{id:"minecraft:invisibility",amplifier:0b,duration:-1,show_particles:0b,show_icon:0b}]}
