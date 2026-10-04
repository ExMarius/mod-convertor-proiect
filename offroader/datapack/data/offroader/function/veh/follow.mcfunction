# Generat de gen_layout.py — nu edita manual.
# 1) indicii de rotire (yaw caroserie + unghi roți) în storage pt macro-uri
scoreboard players operation #cur offr.tmp = @s offr.id
execute store result score @s offr.yaw run data get entity @s Rotation[0] 100
# salvează starea pe caroserie (pt. reconstrucția motorului — veh/revive)
scoreboard players operation #fu offr.tmp = @s offr.fuel
scoreboard players operation #ya offr.tmp = @s offr.yaw
execute as @e[tag=offr_body,distance=..6,limit=1] if score @s offr.id = #cur offr.tmp run scoreboard players operation @s offr.fuel = #fu offr.tmp
execute as @e[tag=offr_body,distance=..6,limit=1] if score @s offr.id = #cur offr.tmp run scoreboard players operation @s offr.yaw = #ya offr.tmp
execute store result score #yaw offr.tmp run data get entity @s Rotation[0] 1
scoreboard players operation #yaw offr.tmp %= #c360 offr.dummy
# Rotation poate fi negativă (ex. -90): aducem în 0..359 înainte de împărțire
execute if score #yaw offr.tmp matches ..-1 run scoreboard players operation #yaw offr.tmp += #c360 offr.dummy
scoreboard players operation #yaw offr.tmp /= #c10 offr.dummy
execute if score #yaw offr.tmp matches 36.. run scoreboard players set #yaw offr.tmp 0
execute if score #flip offr.dummy matches 1.. run scoreboard players add #yaw offr.tmp 18
execute if score #yaw offr.tmp matches 36.. run scoreboard players set #yaw offr.tmp 0
scoreboard players operation #widx offr.tmp = @s offr.wheel
execute if score #spinflip offr.dummy matches 1.. run scoreboard players operation #widx offr.tmp *= #n1 offr.dummy
execute if score #spinflip offr.dummy matches 1.. run scoreboard players add #widx offr.tmp 24
execute if score #widx offr.tmp matches 24.. run scoreboard players set #widx offr.tmp 0
execute store result storage offroader:call y int 1 run scoreboard players get #yaw offr.tmp
execute store result storage offroader:call w int 1 run scoreboard players get #widx offr.tmp
# 2) poziționează fiecare urmăritor (offseturi locale față de cal)
execute at @s as @e[tag=offr_body,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_body
execute at @s as @e[tag=offr_swheel,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_swheel
# offr_w0: yaw + direcție (roată față)
scoreboard players operation #y2 offr.tmp = #yaw offr.tmp
scoreboard players operation #y2 offr.tmp += @s offr.steer
execute if score #y2 offr.tmp matches ..-1 run scoreboard players add #y2 offr.tmp 36
execute if score #y2 offr.tmp matches 36.. run scoreboard players remove #y2 offr.tmp 36
execute store result storage offroader:call y int 1 run scoreboard players get #y2 offr.tmp
execute at @s as @e[tag=offr_w0,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_w0
execute store result storage offroader:call y int 1 run scoreboard players get #yaw offr.tmp
# offr_w1: yaw + direcție (roată față)
scoreboard players operation #y2 offr.tmp = #yaw offr.tmp
scoreboard players operation #y2 offr.tmp += @s offr.steer
execute if score #y2 offr.tmp matches ..-1 run scoreboard players add #y2 offr.tmp 36
execute if score #y2 offr.tmp matches 36.. run scoreboard players remove #y2 offr.tmp 36
execute store result storage offroader:call y int 1 run scoreboard players get #y2 offr.tmp
execute at @s as @e[tag=offr_w1,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_w1
execute store result storage offroader:call y int 1 run scoreboard players get #yaw offr.tmp
execute at @s as @e[tag=offr_w2,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_w2
execute at @s as @e[tag=offr_w3,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_w3
execute at @s as @e[tag=offr_name,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_name
execute at @s as @e[tag=offr_s1,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_s1
execute at @s as @e[tag=offr_s2,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_s2
execute at @s as @e[tag=offr_s3,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_s3
execute at @s as @e[tag=offr_i0,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_i0
execute at @s as @e[tag=offr_i1,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_i1
execute at @s as @e[tag=offr_i2,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_i2
execute at @s as @e[tag=offr_i3,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_offr_i3
# 3) verifică click-urile pe scaune (interaction entities)
execute at @s as @e[tag=offr_i_driver,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/check_driver_i
execute at @s as @e[tag=offr_i_seat,distance=..64] if score @s offr.id = #cur offr.tmp run function offroader:veh/check_seat_i
