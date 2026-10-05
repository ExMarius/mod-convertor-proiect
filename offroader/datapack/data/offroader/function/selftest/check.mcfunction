# Raportează verdictul: mesajul în storage offroader:st msg, rezultatul în #ok offr.tmp.
$execute if score #ok offr.tmp matches 1 run tellraw @a[tag=offr_tester] [{"text":"  [OK] ","color":"green","bold":true},{"text":"$(msg)","color":"white"}]
$execute if score #ok offr.tmp matches 0 run tellraw @a[tag=offr_tester] [{"text":"  [ESEC] ","color":"red","bold":true},{"text":"$(msg)","color":"red"}]
$execute if score #ok offr.tmp matches 1 run say [TEST OK] $(msg)
$execute if score #ok offr.tmp matches 0 run say [TEST ESEC] $(msg)
execute if score #ok offr.tmp matches 1 run scoreboard players add #pass offr.tmp 1
execute if score #ok offr.tmp matches 0 run scoreboard players add #fail offr.tmp 1
