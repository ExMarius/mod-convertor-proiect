# Dispatcher programat — reia contextul jucătorului tester la fiecare pas.
execute as @a[tag=offr_tester,limit=1] at @s run function offroader:selftest/cur with storage offroader:st
execute unless entity @a[tag=offr_tester] run tellraw @a [{"text":"[Offroader TEST] ","color":"aqua","bold":true},{"text":"anulat — testerul a plecat de pe server.","color":"gray"}]
