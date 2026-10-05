# PAS 1: scoatem mașina din garaj (ca și cum am folosi cheia)
function offroader:veh/spawn

execute store result score #ok offr.tmp if entity @e[type=minecraft:horse,tag=offr_veh,limit=1]
data modify storage offroader:st msg set value "vehiculul s-a invocat (calul invizibil exista)"
function offroader:selftest/check with storage offroader:st

scoreboard players set #cnt offr.tmp 0
execute as @e[tag=offr_f] run scoreboard players add #cnt offr.tmp 1
execute store result score #ok offr.tmp if score #cnt offr.tmp matches 14
data modify storage offroader:st msg set value "14 entitati-urmaritor: caroserie + volan + 4 roti + nume + 3 scaune + 4 hitbox-uri"
function offroader:selftest/check with storage offroader:st

execute store result score #ok offr.tmp if score @e[type=minecraft:horse,tag=offr_veh,limit=1] offr.fuel matches 600
data modify storage offroader:st msg set value "rezervor plin la spawn (fuel=600)"
function offroader:selftest/check with storage offroader:st

# chemăm tick-ul DIRECT: dacă funcția e compilată, #hb sare la 1+
function offroader:tick
execute store result score #ok offr.tmp if score #hb offr.dummy matches 1..
data modify storage offroader:st msg set value "functia tick exista si ruleaza chemata direct"
function offroader:selftest/check with storage offroader:st

# salvăm heartbeat-ul ca să verificăm în pasul 2 că TAG-ul tick rulează
scoreboard players operation #hb1 offr.tmp = #hb offr.dummy
data modify storage offroader:st p set value "step2"
schedule function offroader:selftest/step 10t
