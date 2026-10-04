# PAS 7: parcare, iteme, depozitare
execute store result score #nai offr.tmp run data get entity @e[type=minecraft:horse,tag=offr_veh,limit=1] NoAI
execute if score #nai offr.tmp matches 1 run scoreboard players set #ok offr.tmp 1
execute if score #nai offr.tmp matches 0 run scoreboard players set #ok offr.tmp 0
data modify storage offroader:st msg set value "oprit si parcat (nu mai pleaca singur)"
function offroader:selftest/check with storage offroader:st

execute store result score #sp offr.tmp run data get entity @e[type=minecraft:horse,tag=offr_veh,limit=1] attributes[{id:"minecraft:movement_speed"}].base 10000
execute store result score #ok offr.tmp if score #sp offr.tmp matches ..100
data modify storage offroader:st msg set value "viteza zero in parcare"
function offroader:selftest/check with storage offroader:st

# scoatem itemele offroader din teste anterioare (inventarul poate fi plin)
clear @s minecraft:warped_fungus_on_a_stick[item_model="offroader:key"]
clear @s minecraft:carrot_on_a_stick[item_model="offroader:steering_wheel"]
clear @s minecraft:fishing_rod[item_model="offroader:jerrycan"]
function offroader:give
execute store result score #ok offr.tmp if items entity @s contents minecraft:warped_fungus_on_a_stick
data modify storage offroader:st msg set value "give a dat itemele (functia ruleaza)"
function offroader:selftest/check with storage offroader:st
execute store result score #ok offr.tmp if items entity @s contents minecraft:warped_fungus_on_a_stick[item_model="offroader:key"]
data modify storage offroader:st msg set value "cheia primita si recunoscuta (item_model corect)"
function offroader:selftest/check with storage offroader:st

execute store result score #ok offr.tmp if items entity @s contents minecraft:carrot_on_a_stick[item_model="offroader:steering_wheel"]
data modify storage offroader:st msg set value "volanul primit si recunoscut"
function offroader:selftest/check with storage offroader:st

execute store result score #ok offr.tmp if items entity @s contents minecraft:fishing_rod[item_model="offroader:jerrycan"]
data modify storage offroader:st msg set value "bidonul primit si recunoscut"
function offroader:selftest/check with storage offroader:st

execute as @e[type=minecraft:horse,tag=offr_veh,distance=..5,limit=1,sort=nearest] at @s run function offroader:veh/store
execute unless entity @e[type=minecraft:horse,tag=offr_veh,limit=1] run scoreboard players set #ok offr.tmp 1
execute if entity @e[type=minecraft:horse,tag=offr_veh,limit=1] run scoreboard players set #ok offr.tmp 0
data modify storage offroader:st msg set value "masina s-a depozitat (cal + piese eliminate)"
function offroader:selftest/check with storage offroader:st

data modify storage offroader:st p set value "step8"
schedule function offroader:selftest/step 10t
