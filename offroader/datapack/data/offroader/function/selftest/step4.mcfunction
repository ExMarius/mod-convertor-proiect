# PAS 4: viteza de boost aplicată + mișcăm mașina (fără pasager — niciodată
# nu teleportăm un vehicul cu cineva pe el: asta desincronizează jucătorul
# și pare că „cazi din mapă")
execute store result score #sp offr.tmp run data get entity @e[type=minecraft:horse,tag=offr_veh,limit=1] attributes[{id:"minecraft:movement_speed"}].base 10000
execute store result score #ok offr.tmp if score #sp offr.tmp matches 5400..5600
data modify storage offroader:st msg set value "viteza de boost aplicata (0.55)"
function offroader:selftest/check with storage offroader:st

# coborâm întâi (sigur), apoi mutăm mașina 8 blocuri mai încolo
ride @s dismount
execute at @e[type=minecraft:horse,tag=offr_veh,limit=1] run tp @e[type=minecraft:horse,tag=offr_veh,limit=1] ^ ^ ^8 90 0
data modify storage offroader:st p set value "step5"
schedule function offroader:selftest/step 10t
