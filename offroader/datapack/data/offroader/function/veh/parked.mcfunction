# Mașina e parcată (fără șofer) — rulează ca și la poziția calului.
# oprire (o singură dată, la coborâre): frigă motorul + sunet de oprire
execute if score @s offr.wasdriven matches 1 run data merge entity @s {NoAI:1b}
execute if score @s offr.wasdriven matches 1 run playsound offroader:stop master @a[distance=..32] ~ ~ ~ 1 1
scoreboard players set @s offr.wasdriven 0
scoreboard players set @s offr.boost 0
