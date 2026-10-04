# BOOST (click cu volanul) — rulează ca vehiculul.
execute if score @s offr.fuel matches 1.. run scoreboard players set @s offr.boost 60
execute if score @s offr.fuel matches 1.. run playsound offroader:boost master @a[distance=..32] ~ ~ ~ 1.6 1
execute if score @s offr.fuel matches 1.. on passengers run title @s actionbar {"text":"BOOST!","color":"red","bold":true}
execute unless score @s offr.fuel matches 1.. on passengers run title @s actionbar {"text":"Fără combustibil! Alimentează cu bidonul.","color":"dark_red"}
execute unless score @s offr.fuel matches 1.. run playsound offroader:stop master @a[distance=..16] ~ ~ ~ 0.8 1.6
