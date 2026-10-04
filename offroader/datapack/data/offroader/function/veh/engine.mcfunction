# Sunetul motorului — pitch-ul crește cu viteza.
# ralenti (stai pe loc)
execute if score @s offr.speed2 matches ..24 run playsound offroader:engine master @a[distance=..24] ~ ~ ~ 1.5 0.85
# în mișcare: pitch = 0.9 + speed2 * 0.05 / 1000  (macro)
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp = @s offr.speed2
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp *= #c5 offr.dummy
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp /= #c100 offr.dummy
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp += #c900 offr.dummy
execute if score @s offr.speed2 matches 25.. store result storage offroader:call p double 0.001 run scoreboard players get #p offr.tmp
execute if score @s offr.speed2 matches 25.. run function offroader:veh/engine_play with storage offroader:call
