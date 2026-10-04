# Tick-ul principal (totul per-vehicul pornește din veh/tick).
# resigilează NBT-ul calului orice s-ar întâmpla (invizibil + invulnerabil)
data merge entity @e[type=minecraft:horse,tag=offr_veh] {Invulnerable:1b,Invisible:1b,Silent:1b,Persistent:1b}
# dacă motorul (calul) a fost distrus -> reconstruit automat din caroserie
execute as @e[tag=offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] run function offroader:veh/revive
# piese cu adevărat orfane (fără cal ȘI fără caroserie) -> curățate
execute as @e[tag=offr_f,tag=!offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] unless entity @e[tag=offr_body,distance=..10] run kill @s
execute as @e[type=minecraft:horse,tag=offr_veh] at @s run function offroader:veh/tick
