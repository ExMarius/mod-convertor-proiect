# Mașina e parcată (fără șofer) — rulează ca și la poziția calului.
# oprire (o singură dată, la coborâre): frigă motorul + sunet de oprire + viteza 0
execute if score @s offr.wasdriven matches 1 run data merge entity @s {NoAI:1b}
execute if score @s offr.wasdriven matches 1 run attribute @s minecraft:movement_speed base set 0.0
execute if score @s offr.wasdriven matches 1 run scoreboard players set @s offr.applied 0
execute if score @s offr.wasdriven matches 1 run playsound offroader:stop master @a[distance=..32] ~ ~ ~ 1 1
scoreboard players set @s offr.wasdriven 0
scoreboard players set @s offr.boost 0
