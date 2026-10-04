# (rulează CA roata w0) distanța pătrată față de cal, în cm²
execute store result score #wx offr.tmp run data get entity @s Pos[0] 100
execute store result score #wz offr.tmp run data get entity @s Pos[2] 100
scoreboard players operation #dx offr.tmp = #wx offr.tmp
scoreboard players operation #dx offr.tmp -= #hx offr.tmp
scoreboard players operation #dx offr.tmp *= #dx offr.tmp
scoreboard players operation #dz offr.tmp = #wz offr.tmp
scoreboard players operation #dz offr.tmp -= #hz offr.tmp
scoreboard players operation #dz offr.tmp *= #dz offr.tmp
scoreboard players operation #dx offr.tmp += #dz offr.tmp
execute store result score #ok offr.tmp if score #dx offr.tmp matches 150..320
data modify storage offroader:st msg set value "roata fata-stanga e la locul ei (dist. ~1.5 blocuri de cal)"
function offroader:selftest/check with storage offroader:st
