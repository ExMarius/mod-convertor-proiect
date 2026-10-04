# Cheia offroader-ului (click-dreapta) — rulează ca jucătorul, la poziția lui.
scoreboard players set @s offr.key 0

# 1) șofezi -> claxon (funcția rulează ca vehiculul)
execute on vehicle if entity @s[type=minecraft:horse,tag=offr_veh] run function offroader:veh/horn
# 2) ești pasager -> claxon
execute on vehicle if entity @s[type=minecraft:armor_stand,tag=offr_seat] run playsound offroader:horn master @a[distance=..24] ~ ~ ~ 1.2 1
# 3) erai pe offroader -> gata, nu spawnăm/nu depozităm
execute on vehicle if entity @s[tag=offr_veh] run return 1
execute on vehicle if entity @s[tag=offr_seat] run return 1

# 4) offroader în apropiere (stai pe jos lângă el) -> depozitează-l
execute as @e[type=minecraft:horse,tag=offr_veh,distance=..5,limit=1,sort=nearest] at @s run function offroader:veh/store

# 5) nimic în apropiere -> scoate un offroader nou
execute unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..5] run function offroader:veh/spawn
