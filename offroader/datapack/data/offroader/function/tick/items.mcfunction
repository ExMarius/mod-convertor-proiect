# Click-dreapta cu itemele custom (verificăm și modelul din mână).
# Când pluginul e activ (#plugin=1), interacțiunile le tratează pluginul.
execute if score #plugin offr.dummy matches ..0 as @a[scores={offr.key=1..}] at @s if items entity @s weapon.mainhand minecraft:warped_fungus_on_a_stick[item_model="offroader:key"] run function offroader:item_use/key
execute if score #plugin offr.dummy matches ..0 as @a[scores={offr.throttle=1..}] at @s if items entity @s weapon.mainhand minecraft:carrot_on_a_stick[item_model="offroader:steering_wheel"] run function offroader:item_use/throttle
execute if score #plugin offr.dummy matches ..0 as @a[scores={offr.can=1..}] at @s if items entity @s weapon.mainhand minecraft:fishing_rod[item_model="offroader:jerrycan"] run function offroader:item_use/jerrycan
# consumă trigger-ele rămase (inclusiv iteme vanilla cu același tip)
scoreboard players set @a[scores={offr.key=1..}] offr.key 0
scoreboard players set @a[scores={offr.throttle=1..}] offr.throttle 0
scoreboard players set @a[scores={offr.can=1..}] offr.can 0
