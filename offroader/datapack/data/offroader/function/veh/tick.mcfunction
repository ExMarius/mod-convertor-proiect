# Tick-ul vehiculului — rulează ca și la poziția calului.
# cooldown claxon
execute if score @s offr.horncd matches 1.. run scoreboard players remove @s offr.horncd 1

# are șofer? (pasager direct al calului = șoferul)
scoreboard players set #driven offr.tmp 0
execute if entity @s[nbt={Passengers:[{}]}] run scoreboard players set #driven offr.tmp 1
execute if score #driven offr.tmp matches 1 run function offroader:veh/driving
execute if score #driven offr.tmp matches 0 run function offroader:veh/parked

# caroseria, roțile, scaunele și click-urile — mereu
function offroader:veh/follow
