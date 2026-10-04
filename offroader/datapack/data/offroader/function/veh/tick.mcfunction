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
