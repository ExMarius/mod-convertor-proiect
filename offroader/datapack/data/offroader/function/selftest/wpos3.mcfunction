# (rulează CA caroseria) înălțimea față de cal, în cm — raportată în mesaj
execute store result score #by offr.tmp run data get entity @s Pos[1] 100
scoreboard players operation #dy offr.tmp = #by offr.tmp
scoreboard players operation #dy offr.tmp -= #hy offr.tmp
execute if score #dy offr.tmp matches ..-1 run scoreboard players operation #dy offr.tmp *= #n1 offr.dummy
execute store result storage offroader:st h int 1 run scoreboard players get #dy offr.tmp
execute store result score #ok offr.tmp if score #dy offr.tmp matches 15..60
$data modify storage offroader:st msg set value "caroseria: la $(h) cm deasupra calului (corect: 15..60)"
function offroader:selftest/check with storage offroader:st
