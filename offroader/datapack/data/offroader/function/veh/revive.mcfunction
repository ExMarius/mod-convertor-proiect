# Reconstruiește calul (motorul) distrus — rulează CA și LA caroserie (offr_body).
# Starea (combustibil, unghi, poziția) e salvată pe caroserie de veh/follow.
scoreboard players operation #cur offr.tmp = @s offr.id
scoreboard players operation #fu offr.tmp = @s offr.fuel
scoreboard players operation #ya offr.tmp = @s offr.yaw
execute store result score #px offr.tmp run data get entity @s Pos[0] 100
execute store result score #pz offr.tmp run data get entity @s Pos[2] 100

summon minecraft:horse ~ ~ ~ {Tags:["offr_veh","offr_new"],Tame:1b,Silent:1b,Invulnerable:1b,Invisible:1b,PersistenceRequired:1b,NoAI:1b,active_effects:[{id:"minecraft:invisibility",amplifier:0b,duration:-1,show_particles:0b,show_icon:0b}],SaddleItem:{id:"minecraft:saddle",count:1},attributes:[{id:"minecraft:movement_speed",base:0.3375},{id:"minecraft:jump_strength",base:0.85},{id:"minecraft:max_health",base:30}],Health:30f}

# orientarea și starea, restaurate
execute store result entity @e[tag=offr_new,limit=1] Rotation[0] float 0.1 run scoreboard players get #ya offr.tmp
scoreboard players operation @e[tag=offr_new,limit=1] offr.id = #cur offr.tmp
scoreboard players set @e[tag=offr_new,limit=1] offr.wheel 0
scoreboard players set @e[tag=offr_new,limit=1] offr.boost 0
scoreboard players set @e[tag=offr_new,limit=1] offr.ticks 0
scoreboard players set @e[tag=offr_new,limit=1] offr.mode 1
scoreboard players set @e[tag=offr_new,limit=1] offr.applied 1
scoreboard players set @e[tag=offr_new,limit=1] offr.wasdriven 0
scoreboard players set @e[tag=offr_new,limit=1] offr.horncd 0
scoreboard players set @e[tag=offr_new,limit=1] offr.steer 0
scoreboard players operation @e[tag=offr_new,limit=1] offr.cyaw = #ya offr.tmp
scoreboard players operation @e[tag=offr_new,limit=1] offr.x = #px offr.tmp
scoreboard players operation @e[tag=offr_new,limit=1] offr.z = #pz offr.tmp
scoreboard players operation @e[tag=offr_new,limit=1] offr.x0 = #px offr.tmp
scoreboard players operation @e[tag=offr_new,limit=1] offr.z0 = #pz offr.tmp
scoreboard players operation @e[tag=offr_new,limit=1] offr.fuel = #fu offr.tmp
tag @e[tag=offr_new] remove offr_new

# feedback: sunetul „destroyed" din mod + fum + mesaj
playsound offroader:destroyed master @a[distance=..24] ~ ~ ~ 1 1
particle minecraft:poof ~ ~1 ~ 0.5 0.5 0.5 0.05 20
tellraw @a[distance=..24] {"text":"[Offroader] Motor distrus — reconstruit automat! Urcă din nou la volan.","color":"red"}
