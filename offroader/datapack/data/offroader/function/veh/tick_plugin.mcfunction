# MOD PLUGIN ACTIV — doar vizualele; fizica/motorul/combustibilul/HUD-ul
# sunt în OffroaderPlugin (care scrie direct offr.steer = unghiul real).

# viteza reală (pt roți + spin)
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

# cronometru
scoreboard players add @s offr.ticks 1
execute if score @s offr.ticks matches 20.. run scoreboard players set @s offr.ticks 0

# unghiul calului (zecimi de grad), normalizat
execute store result score @s offr.hyaw run data get entity @s Rotation[0] 10
execute if score @s offr.hyaw matches ..-1 run scoreboard players operation @s offr.hyaw += #c3600 offr.dummy
execute if score @s offr.hyaw matches 3600.. run scoreboard players operation @s offr.hyaw -= #c3600 offr.dummy

# cyaw = unghiul calului DIRECT (pluginul face deja virajul progresiv,
# ca în mod — corpul se rotește exact cu entitatea)
scoreboard players operation @s offr.cyaw = @s offr.hyaw

# roțile se învârt după viteza reală (chiar și fără șofer)
execute if score @s offr.speed2 matches 25.. run scoreboard players add @s offr.wheel 1
execute if score @s offr.speed2 matches 400.. run scoreboard players add @s offr.wheel 1
execute if score @s offr.speed2 matches 2500.. run scoreboard players add @s offr.wheel 2
execute if score @s offr.wheel matches 24.. run scoreboard players remove @s offr.wheel 24

# caroseria, roțile, scaunele — mereu
function offroader:veh/follow
