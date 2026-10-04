# PAS 8: curățenie + rezumat
execute unless entity @e[tag=offr_f] run scoreboard players set #ok offr.tmp 1
execute if entity @e[tag=offr_f] run scoreboard players set #ok offr.tmp 0
data modify storage offroader:st msg set value "urmasii orfani curatati automat"
function offroader:selftest/check with storage offroader:st

tellraw @s [{"text":"[Offroader TEST] FINAL: ","color":"aqua","bold":true},{"score":{"name":"#pass","objective":"offr.tmp"},"color":"green","bold":true},{"text":" trecute, ","color":"white"},{"score":{"name":"#fail","objective":"offr.tmp"},"color":"red","bold":true},{"text":" esuate.","color":"white"}]
execute if score #fail offr.tmp matches 0 run tellraw @s {"text":"TOTUL VERDE! Trimite-mi lista + ce vezi cu ochii (model, sunete, pozitia soferului).","color":"green","bold":true}
execute if score #fail offr.tmp matches 1.. run tellraw @s {"text":"SUNT ERORI - copiaza toata lista de mai sus si trimite-mi-o.","color":"red","bold":true}
tag @s remove offr_tester
data remove storage offroader:st p
