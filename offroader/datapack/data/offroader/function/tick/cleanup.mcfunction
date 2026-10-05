# Piese cu adevărat orfane (fără cal ȘI fără caroserie) -> curățate.
execute as @e[tag=offr_f,tag=!offr_body] at @s unless entity @e[type=minecraft:horse,tag=offr_veh,distance=..10] unless entity @e[tag=offr_body,distance=..10] run kill @s
