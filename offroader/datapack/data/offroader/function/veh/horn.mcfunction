# Claxon (rulează ca vehiculul).
execute if score @s offr.horncd matches ..0 run playsound offroader:horn master @a[distance=..32] ~ ~ ~ 2 1
execute if score @s offr.horncd matches ..0 run scoreboard players set @s offr.horncd 8
