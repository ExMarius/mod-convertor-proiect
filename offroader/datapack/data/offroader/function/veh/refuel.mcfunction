# Alimentare (rulează ca vehiculul). +40 combustibil, max 100.
execute if score @s offr.fuel matches ..99 run scoreboard players add @s offr.fuel 40
execute if score @s offr.fuel matches 101.. run scoreboard players set @s offr.fuel 100
execute if score @s offr.fuel matches ..99 run playsound offroader:slosh master @a[distance=..16] ~ ~ ~ 1 1
execute if score @s offr.fuel matches ..99 run title @a[distance=..6] actionbar {"text":"+40 combustibil!","color":"green"}
execute if score @s offr.fuel matches 100 run title @a[distance=..6] actionbar {"text":"Rezervorul e deja plin.","color":"yellow"}
