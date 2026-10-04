# Mașina e condusă — rulează ca și la poziția calului.
# (viteza, cronometrul și roțile se calculează în veh/tick)
# pornire (o singură dată, la urcarea în mașină)
execute if score @s offr.wasdriven matches 0 run data merge entity @s {NoAI:0b}
execute if score @s offr.wasdriven matches 0 run playsound offroader:start master @a[distance=..32] ~ ~ ~ 1.2 1
scoreboard players set @s offr.wasdriven 1

# unghiul de direcție: cât de repede virează calul (pentru roțile față)
execute store result score @s offr.yaw run data get entity @s Rotation[0] 100
scoreboard players operation #dyaw offr.tmp = @s offr.yaw
scoreboard players operation #dyaw offr.tmp -= @s offr.yaw0
execute if score #dyaw offr.tmp matches ..-18001 run scoreboard players operation #dyaw offr.tmp += #c36000 offr.dummy
execute if score #dyaw offr.tmp matches 18001.. run scoreboard players operation #dyaw offr.tmp -= #c36000 offr.dummy
scoreboard players operation #dyaw offr.tmp *= #c3 offr.dummy
scoreboard players operation #dyaw offr.tmp /= #c500 offr.dummy
execute if score #dyaw offr.tmp matches 8.. run scoreboard players set #dyaw offr.tmp 7
execute if score #dyaw offr.tmp matches ..-8 run scoreboard players set #dyaw offr.tmp -7
scoreboard players operation @s offr.steer = #dyaw offr.tmp
scoreboard players operation @s offr.yaw0 = @s offr.yaw

# consum: 1 combustibil / secundă, doar în mișcare
execute if score @s offr.ticks matches 0 if score @s offr.fuel matches 1.. if score @s offr.speed2 matches 25.. run scoreboard players remove @s offr.fuel 1

# mod de viteză: 0 = fără combustibil, 1 = croazieră, 2 = boost
execute if score @s offr.fuel matches 1.. run scoreboard players set @s offr.mode 1
execute if score @s offr.fuel matches ..0 run scoreboard players set @s offr.mode 0
execute if score @s offr.boost matches 1.. if score @s offr.fuel matches 1.. run scoreboard players set @s offr.mode 2
execute if score @s offr.boost matches 1.. run scoreboard players remove @s offr.boost 1
execute if score @s offr.mode != @s offr.applied run function offroader:veh/apply_mode

# sunet de motor + HUD o dată pe secundă
execute if score @s offr.ticks matches 0 if score @s offr.fuel matches 1.. run function offroader:veh/engine
execute if score @s offr.ticks matches 0 run function offroader:veh/hud
