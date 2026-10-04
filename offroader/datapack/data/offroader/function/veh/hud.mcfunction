# HUD pentru șofer (actionbar): combustibil + viteză aproximativă.
execute if score @s offr.speed2 matches ..24 run scoreboard players set #kmh offr.tmp 0
execute if score @s offr.speed2 matches 25..299 run scoreboard players set #kmh offr.tmp 7
execute if score @s offr.speed2 matches 300..1199 run scoreboard players set #kmh offr.tmp 15
execute if score @s offr.speed2 matches 1200..3599 run scoreboard players set #kmh offr.tmp 28
execute if score @s offr.speed2 matches 3600..7499 run scoreboard players set #kmh offr.tmp 45
execute if score @s offr.speed2 matches 7500..11999 run scoreboard players set #kmh offr.tmp 65
execute if score @s offr.speed2 matches 12000.. run scoreboard players set #kmh offr.tmp 83
scoreboard players operation #f offr.tmp = @s offr.fuel
scoreboard players operation #f offr.tmp /= #c6 offr.dummy
execute store result storage offroader:call f int 1 run scoreboard players get #f offr.tmp
execute store result storage offroader:call k int 1 run scoreboard players get #kmh offr.tmp
execute if score @s offr.fuel matches 120.. on passengers run function offroader:veh/hud_ok with storage offroader:call
execute if score @s offr.fuel matches ..119 on passengers run function offroader:veh/hud_low with storage offroader:call
