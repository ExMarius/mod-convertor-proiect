# Aplică atributele potrivite modului de viteză (doar la schimbare).
execute if score @s offr.mode matches 2 run attribute @s minecraft:movement_speed base set 0.55
execute if score @s offr.mode matches 1 run attribute @s minecraft:movement_speed base set 0.3375
execute if score @s offr.mode matches 0 run attribute @s minecraft:movement_speed base set 0.0
execute if score @s offr.mode matches 0 run playsound offroader:stop master @a[distance=..32] ~ ~ ~ 1 0.7
scoreboard players operation @s offr.applied = @s offr.mode
