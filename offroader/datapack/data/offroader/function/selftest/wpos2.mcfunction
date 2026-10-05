# (rulează CA roata w0) distanța pătrată față de cal, în cm² — raportată în mesaj
execute store result score #wx offr.tmp run data get entity @s Pos[0] 100
execute store result score #wz offr.tmp run data get entity @s Pos[2] 100
scoreboard players operation #dx offr.tmp = #wx offr.tmp
scoreboard players operation #dx offr.tmp -= #hx offr.tmp
scoreboard players operation #dx offr.tmp *= #dx offr.tmp
scoreboard players operation #dz offr.tmp = #wz offr.tmp
scoreboard players operation #dz offr.tmp -= #hz offr.tmp
scoreboard players operation #dz offr.tmp *= #dz offr.tmp
scoreboard players operation #dx offr.tmp += #dz offr.tmp
execute store result storage offroader:st d int 1 run scoreboard players get #dx offr.tmp
execute store result score #ok offr.tmp if score #dx offr.tmp matches 38000..43000
$data modify storage offroader:st msg set value "roata fata-stanga: dist²=$(d) cm² (corect: 38000..43000)"
function offroader:selftest/check with storage offroader:st
