# Bucla principală (20/s). Ordinea contează: întâi acțiunile jucătorilor
# (spawn/boost/alimentare), apoi actualizarea vehiculelor.

# --- click-dreapta cu itemele custom (verificăm și modelul din mână) ---
execute as @a[scores={offr.key=1..}] at @s if items entity @s weapon.mainhand minecraft:warped_fungus_on_a_stick[minecraft:item_model="offroader:key"] run function offroader:item_use/key
execute as @a[scores={offr.throttle=1..}] at @s if items entity @s weapon.mainhand minecraft:carrot_on_a_stick[minecraft:item_model="offroader:steering_wheel"] run function offroader:item_use/throttle
execute as @a[scores={offr.can=1..}] at @s if items entity @s weapon.mainhand minecraft:fishing_rod[minecraft:item_model="offroader:jerrycan"] run function offroader:item_use/jerrycan

# consumă trigger-ele rămase (inclusiv iteme vanilla cu același tip)
scoreboard players set @a[scores={offr.key=1..}] offr.key 0
scoreboard players set @a[scores={offr.throttle=1..}] offr.throttle 0
scoreboard players set @a[scores={offr.can=1..}] offr.can 0

# --- bucla vehiculelor ---
execute as @e[type=minecraft:horse,tag=offr_veh] at @s run function offroader:veh/tick

# --- siguranță: urmăritori orfani (cal dispărut) se curăță singuri ---
execute as @e[tag=offr_f] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] run kill @s
