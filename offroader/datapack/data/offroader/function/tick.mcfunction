# Tick-ul principal (totul per-vehicul pornește din veh/tick).
# resigilează NBT-ul calului (DOAR câmpuri valide pe 26.3 — Invisible nu mai
# există pentru mobs, iar câmpuri invalide omoară funcția la încărcare!)
data merge entity @e[type=minecraft:horse,tag=offr_veh] {Invulnerable:1b,Silent:1b,PersistenceRequired:1b,active_effects:[{id:"minecraft:invisibility",amplifier:0b,duration:-1,show_particles:0b,show_icon:0b}]}
# dacă motorul (calul) a fost distrus -> reconstruit automat din caroserie
execute as @e[tag=offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] run function offroader:veh/revive
# piese cu adevărat orfane (fără cal ȘI fără caroserie) -> curățate
execute as @e[tag=offr_f,tag=!offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] unless entity @e[tag=offr_body,distance=..10] run kill @s
execute as @e[type=minecraft:horse,tag=offr_veh] at @s run function offroader:veh/tick
