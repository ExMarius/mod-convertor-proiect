# Intrarea tag-ului minecraft:tick — MINIMALĂ, practic imposibil de stricat.
# Corpul e în fișiere separate: o eroare de compilare într-una nu oprește
# restul (heartbeat-ul rămâne viu și vedem exact ce pică în log).
scoreboard players add #hb offr.dummy 1
function offroader:tick/main
