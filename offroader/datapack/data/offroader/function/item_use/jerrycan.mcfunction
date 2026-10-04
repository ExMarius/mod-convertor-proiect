# Bidonul de combustibil (click-dreapta lângă vehicul). Rulează ca jucătorul.
scoreboard players set @s offr.can 0
# nu vrem să pescuim: scăpăm de plută imediat
kill @e[type=minecraft:fishing_bobber,distance=..4]
# alimentează cel mai apropiat offroader (<= 5 blocuri)
execute as @e[type=minecraft:horse,tag=offr_veh,distance=..5,limit=1,sort=nearest] at @s run function offroader:veh/refuel
