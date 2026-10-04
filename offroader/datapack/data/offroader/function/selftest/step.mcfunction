# Dispatcher programat — reia contextul jucătorului tester la fiecare pas.
execute as @a[tag=offr_tester,limit=1] at @s if data storage offroader:st p run function offroader:selftest/cur with storage offroader:st
