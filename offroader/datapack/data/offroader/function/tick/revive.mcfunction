# Motor distrus -> reconstruit automat din caroserie.
execute as @e[tag=offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] run function offroader:veh/revive
