# Alimentare (rulează ca vehiculul). +40 combustibil, max 100.
execute if score @s offr.fuel matches ..479 run scoreboard players add @s offr.fuel 120
execute if score @s offr.fuel matches 481.. run scoreboard players set @s offr.fuel 600
execute if score @s offr.fuel matches ..479 run playsound offroader:slosh master @a[distance=..16] ~ ~ ~ 1 1
execute if score @s offr.fuel matches ..99 run title @a[distance=..6] actionbar {"text":"+20% combustibil!","color":"green"}
execute if score @s offr.fuel matches 480.. run title @a[distance=..6] actionbar {"text":"Rezervorul e deja plin.","color":"yellow"}
