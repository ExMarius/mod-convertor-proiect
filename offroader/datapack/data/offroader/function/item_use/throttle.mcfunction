# Volanul (click-dreapta în timp ce șofezi) = BOOST. Rulează ca jucătorul.
scoreboard players set @s offr.throttle 0
execute on vehicle if entity @s[type=minecraft:horse,tag=offr_veh] run function offroader:veh/boost
