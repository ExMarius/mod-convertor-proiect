# Demontare efectivă — rulează ca și la poziția calului.
scoreboard players operation #cur offr.tmp = @s offr.id
execute as @e[tag=offr_f,distance=..16] if score @s offr.id = #cur offr.tmp run kill @s
playsound offroader:stop master @a[distance=..16] ~ ~ ~ 1 1
title @a[distance=..8] actionbar {"text":"[Offroader] Depozitat.","color":"yellow"}
kill @s
