# Detectează click-dreapta pe scaunul șoferului — rulează ca interaction-ul.
scoreboard players set #tsn offr.tmp 0
execute store result score #tsn offr.tmp run data get entity @s interaction.timestamp
execute if score #tsn offr.tmp = @s offr.ts run return 1
scoreboard players operation @s offr.ts = #tsn offr.tmp
execute store result storage offroader:call id int 1 run scoreboard players get @s offr.id
execute on target run function offroader:veh/board_driver with storage offroader:call
