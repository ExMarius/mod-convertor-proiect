# (rulează CA caroseria) înălțimea față de cal: ~0.35 blocuri = 35 cm
execute store result score #by offr.tmp run data get entity @s Pos[1] 100
scoreboard players operation #dy offr.tmp = #by offr.tmp
scoreboard players operation #dy offr.tmp -= #hy offr.tmp
execute if score #dy offr.tmp matches ..-1 run scoreboard players operation #dy offr.tmp *= #n1 offr.dummy
execute store result score #ok offr.tmp if score #dy offr.tmp matches 15..60
data modify storage offroader:st msg set value "caroseria pluteste la inaltimea corecta (0.35)"
function offroader:selftest/check with storage offroader:st
