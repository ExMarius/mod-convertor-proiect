# Dă setul de obiecte offroader jucătorului care rulează funcția.
# În chat (op): /function offroader:give
# Pentru alt jucător: /execute as NumeJucător run function offroader:give
# (1.21.4: custom_name/lore primesc text JSON ca string)

give @s minecraft:warped_fungus_on_a_stick[item_model="offroader:key",custom_name='{"text":"Cheie Offroader","color":"gold","italic":false}',lore=['{"text":"Click-dreapta: scoate / depozitează offroader-ul","color":"gray","italic":false}','{"text":"Cât ești în mașină: claxon","color":"gray","italic":false}'],enchanted_glint_override=true] 1
give @s minecraft:carrot_on_a_stick[item_model="offroader:steering_wheel",custom_name='{"text":"Volan","color":"yellow","italic":false}',lore=['{"text":"Ține-l în mână în timp ce șofezi (WASD + spațiu)","color":"gray","italic":false}','{"text":"Click-dreapta: BOOST","color":"red","italic":false}'],enchanted_glint_override=true] 1
give @s minecraft:fishing_rod[item_model="offroader:jerrycan",custom_name='{"text":"Bidon combustibil","color":"red","italic":false}',lore=['{"text":"Click-dreapta lângă offroader: alimentare +20%","color":"gray","italic":false}'],enchanted_glint_override=true] 1
tellraw @s {"text":"[Offroader] Ai primit cheia, volanul și bidonul. Folosește cheia ca să scoți mașina!","color":"yellow"}
