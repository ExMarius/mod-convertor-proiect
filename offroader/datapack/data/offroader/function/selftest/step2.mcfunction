# PAS 2: după 10 tick-uri, urmăritorii trebuiau să se așeze pe poziții
scoreboard players set #cnt offr.tmp 0
execute at @e[type=minecraft:horse,tag=offr_veh,limit=1] as @e[tag=offr_f,distance=..4] run scoreboard players add #cnt offr.tmp 1
execute store result score #ok offr.tmp if score #cnt offr.tmp matches 14
data modify storage offroader:st msg set value "toti urmaritorii s-au asezat langa vehicul (teleport relativ)"
function offroader:selftest/check with storage offroader:st

execute store result score #ok offr.tmp run data get entity @e[tag=offr_body,limit=1] item.components."minecraft:item_model"
data modify storage offroader:st msg set value "caroseria foloseste modelul custom (item_model offroader:body)"
function offroader:selftest/check with storage offroader:st

execute store result score #ok offr.tmp run data get entity @e[tag=offr_name,limit=1] text
data modify storage offroader:st msg set value "numele masinii exista (text_display)"
function offroader:selftest/check with storage offroader:st

# urcăm la volan
ride @s mount @e[type=minecraft:horse,tag=offr_veh,limit=1]
data modify storage offroader:st p set value "step3"
schedule function offroader:selftest/step 10t
