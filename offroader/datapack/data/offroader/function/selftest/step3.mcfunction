# PAS 3: pornire motor + boost (suntem la volan)
execute store result score #nai offr.tmp run data get entity @e[type=minecraft:horse,tag=offr_veh,limit=1] NoAI
execute if score #nai offr.tmp matches 0 run scoreboard players set #ok offr.tmp 1
execute if score #nai offr.tmp matches 1.. run scoreboard players set #ok offr.tmp 0
data modify storage offroader:st msg set value "motorul a pornit (calul primeste comenzi WASD)"
function offroader:selftest/check with storage offroader:st

execute store result score #sp offr.tmp run data get entity @e[type=minecraft:horse,tag=offr_veh,limit=1] attributes[{id:"minecraft:movement_speed"}].base 10000
execute store result score #ok offr.tmp if score #sp offr.tmp matches 3300..3450
data modify storage offroader:st msg set value "viteza de croaziera aplicata (0.3375)"
function offroader:selftest/check with storage offroader:st

execute store result score #ok offr.tmp if score @e[type=minecraft:horse,tag=offr_veh,limit=1] offr.wasdriven matches 1
data modify storage offroader:st msg set value "starea 'condus' activa"
function offroader:selftest/check with storage offroader:st

# motor + HUD rulează fără erori (eventualele erori apar în chat/log)
execute as @e[type=minecraft:horse,tag=offr_veh,limit=1] run function offroader:veh/engine
execute as @e[type=minecraft:horse,tag=offr_veh,limit=1] run function offroader:veh/hud

# BOOST
execute as @e[type=minecraft:horse,tag=offr_veh,limit=1] run function offroader:veh/boost
execute store result score #ok offr.tmp if score @e[type=minecraft:horse,tag=offr_veh,limit=1] offr.boost matches 1..
data modify storage offroader:st msg set value "boost activat (3 secunde de viteza)"
function offroader:selftest/check with storage offroader:st

data modify storage offroader:st p set value "step4"
schedule function offroader:selftest/step 10t
