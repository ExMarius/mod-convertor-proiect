# Depozitare — rulează ca și la poziția calului.
execute if entity @s[nbt={Passengers:[{}]}] run title @a[distance=..6] actionbar {"text":"Nu poți depozita un offroader ocupat!","color":"red"}
execute unless entity @s[nbt={Passengers:[{}]}] run function offroader:veh/store_do
