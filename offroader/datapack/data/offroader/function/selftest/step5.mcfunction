# PAS 5: roți, urmărire, alimentare, claxon
execute store result score #ok offr.tmp if score @e[type=minecraft:horse,tag=offr_veh,limit=1] offr.wheel matches 1..
data modify storage offroader:st msg set value "rotile se invart odata cu miscarea"
function offroader:selftest/check with storage offroader:st

scoreboard players set #cnt offr.tmp 0
execute at @e[type=minecraft:horse,tag=offr_veh,limit=1] as @e[tag=offr_f,distance=..4] run scoreboard players add #cnt offr.tmp 1
execute store result score #ok offr.tmp if score #cnt offr.tmp matches 13
data modify storage offroader:st msg set value "caroseria si rotile au urmat masina dupa miscare"
function offroader:selftest/check with storage offroader:st

scoreboard players set @e[type=minecraft:horse,tag=offr_veh,limit=1] offr.fuel 30
execute as @e[type=minecraft:horse,tag=offr_veh,limit=1] run function offroader:veh/refuel
execute store result score #ok offr.tmp if score @e[type=minecraft:horse,tag=offr_veh,limit=1] offr.fuel matches 70
data modify storage offroader:st msg set value "alimentarea adauga +40 combustibil (30 -> 70)"
function offroader:selftest/check with storage offroader:st

execute as @e[type=minecraft:horse,tag=offr_veh,limit=1] run function offroader:veh/horn
execute store result score #ok offr.tmp if score @e[type=minecraft:horse,tag=offr_veh,limit=1] offr.horncd matches 1..
data modify storage offroader:st msg set value "claxonul porneste (cooldown activ)"
function offroader:selftest/check with storage offroader:st

data modify storage offroader:st p set value "step6"
schedule function offroader:selftest/step 10t
