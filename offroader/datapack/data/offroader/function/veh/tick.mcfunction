# Tick-ul vehiculului — rulează ca și la poziția calului.
# cooldown claxon
execute if score @s offr.horncd matches 1.. run scoreboard players remove @s offr.horncd 1

# viteza reală (se măsoară MEREU, chiar și fără șofer — folosită de
# roți, motor și HUD; mișcarea se detectează indiferent cine mută calul)
scoreboard players operation @s offr.x0 = @s offr.x
scoreboard players operation @s offr.z0 = @s offr.z
execute store result score @s offr.x run data get entity @s Pos[0] 100
execute store result score @s offr.z run data get entity @s Pos[2] 100
scoreboard players operation #dx offr.tmp = @s offr.x
scoreboard players operation #dx offr.tmp -= @s offr.x0
scoreboard players operation #dx offr.tmp *= #dx offr.tmp
scoreboard players operation #dz offr.tmp = @s offr.z
scoreboard players operation #dz offr.tmp -= @s offr.z0
scoreboard players operation #dz offr.tmp *= #dz offr.tmp
scoreboard players operation #dx offr.tmp += #dz offr.tmp
scoreboard players operation @s offr.speed2 = #dx offr.tmp

# cronometru (1 secundă = 20 tick-uri)
scoreboard players add @s offr.ticks 1
execute if score @s offr.ticks matches 20.. run scoreboard players set @s offr.ticks 0

# unghiul calului (zecimi de grad), normalizat 0..3599
execute store result score @s offr.hyaw run data get entity @s Rotation[0] 10
execute if score @s offr.hyaw matches ..-1 run scoreboard players operation @s offr.hyaw += #c3600 offr.dummy
execute if score @s offr.hyaw matches 3600.. run scoreboard players operation @s offr.hyaw -= #c3600 offr.dummy

# UNGHIUL MAȘINII (cyaw) urmărește calul cu maxim 4°/tick = 80°/s
# — mașina virează PROGRESIV, ca un vehicul adevărat (nu snap cu mouse-ul)
scoreboard players operation #dy offr.tmp = @s offr.hyaw
scoreboard players operation #dy offr.tmp -= @s offr.cyaw
execute if score #dy offr.tmp matches 1801.. run scoreboard players operation #dy offr.tmp -= #c3600 offr.dummy
execute if score #dy offr.tmp matches ..-1801 run scoreboard players operation #dy offr.tmp += #c3600 offr.dummy
execute if score #dy offr.tmp matches 41.. run scoreboard players set #dy offr.tmp 40
execute if score #dy offr.tmp matches ..-41 run scoreboard players set #dy offr.tmp -40
scoreboard players operation @s offr.cyaw += #dy offr.tmp
execute if score @s offr.cyaw matches 3600.. run scoreboard players operation @s offr.cyaw -= #c3600 offr.dummy
execute if score @s offr.cyaw matches ..-1 run scoreboard players operation @s offr.cyaw += #c3600 offr.dummy

# unghiul vizual al roților față = viteza de virare curentă
scoreboard players operation @s offr.steer = #dy offr.tmp
execute if score @s offr.steer matches 8.. run scoreboard players set @s offr.steer 7
execute if score @s offr.steer matches ..-8 run scoreboard players set @s offr.steer -7

# roțile se învârt după viteza reală (chiar și fără șofer)
execute if score @s offr.speed2 matches 25.. run scoreboard players add @s offr.wheel 1
execute if score @s offr.speed2 matches 400.. run scoreboard players add @s offr.wheel 1
execute if score @s offr.speed2 matches 2500.. run scoreboard players add @s offr.wheel 2
execute if score @s offr.wheel matches 24.. run scoreboard players remove @s offr.wheel 24

# are șofer? numărăm pasagerii calului (execute on passengers — mai
# robust decât potrivirea NBT Passengers)
scoreboard players set #np offr.tmp 0
execute on passengers run scoreboard players add #np offr.tmp 1
execute if score #np offr.tmp matches 1.. run function offroader:veh/driving
execute if score #np offr.tmp matches 0 run function offroader:veh/parked

# caroseria, roțile, scaunele și click-urile — mereu
function offroader:veh/follow
