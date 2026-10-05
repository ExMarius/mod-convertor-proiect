# Sunetul motorului — pitch ca în mod: 0.8 (ralenti) .. 1.6 (viteză max).
# ralenti (stai pe loc cu motorul pornit)
execute if score @s offr.speed2 matches ..24 run playsound offroader:engine master @a[distance=..24] ~ ~ ~ 1.2 0.8
# în mișcare: pitch = 0.8 + speed2*0.16 (macro), max 1.6
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp = @s offr.speed2
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp *= #c16 offr.dummy
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp /= #c100 offr.dummy
execute if score @s offr.speed2 matches 25.. run scoreboard players operation #p offr.tmp += #c800 offr.dummy
execute if score @s offr.speed2 matches 25.. if score #p offr.tmp matches 1601.. run scoreboard players set #p offr.tmp 1600
execute if score @s offr.speed2 matches 25.. store result storage offroader:call p double 0.001 run scoreboard players get #p offr.tmp
execute if score @s offr.speed2 matches 25.. run function offroader:veh/engine_play with storage offroader:call
