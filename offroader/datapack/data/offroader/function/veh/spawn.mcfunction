# Scoate un offroader nou — rulează ca jucătorul, la poziția/rotția lui.
# Calul invizibil = „motorul" (WASD = mers, spațiu = săritură off-road).
summon minecraft:horse ^ ^ ^1.6 {Tags:["offr_veh","offr_new"],Tame:1b,Silent:1b,Invulnerable:1b,Invisible:1b,Persistent:1b,NoAI:1b,SaddleItem:{id:"minecraft:saddle",count:1},CustomName:{text:"Offroader"},attributes:[{id:"minecraft:movement_speed",base:0.3375},{id:"minecraft:jump_strength",base:0.85},{id:"minecraft:max_health",base:30}],Health:30f}

# orientat exact ca jucătorul (2 zecimale)
execute store result entity @e[tag=offr_new,limit=1] Rotation[0] float 0.01 run data get entity @s Rotation[0] 100

# identificator + stare inițială
scoreboard players add #nextid offr.id 1
scoreboard players operation @e[tag=offr_new,limit=1] offr.id = #nextid offr.id
scoreboard players set @e[tag=offr_new,limit=1] offr.fuel 600
scoreboard players set @e[tag=offr_new,limit=1] offr.wheel 0
scoreboard players set @e[tag=offr_new,limit=1] offr.boost 0
scoreboard players set @e[tag=offr_new,limit=1] offr.ticks 0
scoreboard players set @e[tag=offr_new,limit=1] offr.mode 1
scoreboard players set @e[tag=offr_new,limit=1] offr.applied 1
scoreboard players set @e[tag=offr_new,limit=1] offr.wasdriven 0
scoreboard players set @e[tag=offr_new,limit=1] offr.horncd 0
scoreboard players set @e[tag=offr_new,limit=1] offr.steer 0
execute store result score @e[tag=offr_new,limit=1] offr.yaw0 run data get entity @e[tag=offr_new,limit=1] Rotation[0] 100
execute store result score @e[tag=offr_new,limit=1] offr.x run data get entity @e[tag=offr_new,limit=1] Pos[0] 100
execute store result score @e[tag=offr_new,limit=1] offr.z run data get entity @e[tag=offr_new,limit=1] Pos[2] 100
scoreboard players operation @e[tag=offr_new,limit=1] offr.x0 = @e[tag=offr_new,limit=1] offr.x
scoreboard players operation @e[tag=offr_new,limit=1] offr.z0 = @e[tag=offr_new,limit=1] offr.z

# caroseria, roțile, scaunele, interaction-urile
execute as @e[tag=offr_new,limit=1] at @s run function offroader:veh/spawn_followers
tag @e[tag=offr_new] remove offr_new

playsound offroader:start master @a[distance=..24] ~ ~ ~ 1 1
tellraw @s {text:"[Offroader] Scos din garaj! Click-dreapta pe scaunul din față (cel cu volanul) ca să șofezi.",color:"yellow"}
