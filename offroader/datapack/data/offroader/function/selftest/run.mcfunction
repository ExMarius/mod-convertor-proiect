# TEST AUTOMAT — se rulează de un jucător (op): /function offroader:selftest
# Parcurge viața completă a mașinii în ~5 secunde și raportează [OK]/[EȘEC].
# ATENȚIE: șterge vehiculele offroader aflate la maxim 24 de blocuri!
# oprește orice pas programat dintr-un test anterior
schedule clear offroader:selftest/step
tag @s add offr_tester
scoreboard players set #pass offr.tmp 0
scoreboard players set #fail offr.tmp 0
execute at @s run kill @e[type=minecraft:horse,tag=offr_veh,distance=..24]
execute at @s run kill @e[tag=offr_f,distance=..24]
tellraw @s [{"text":"[Offroader TEST] ","color":"aqua","bold":true},{"text":"pornesc testele (~5 s) — nu te mișca între timp...","color":"white"}]
data modify storage offroader:st p set value "step1"
function offroader:selftest/cur with storage offroader:st
