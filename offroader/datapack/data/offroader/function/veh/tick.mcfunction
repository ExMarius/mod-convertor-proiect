# Dispatcher: când pluginul e activ (#plugin=1) el face fizica, combustibilul,
# sunetele și HUD-ul — datapack-ul doar poziționează vizualele.
# Fără plugin: comportamentul vechi integral (fallback).
execute if score #plugin offr.dummy matches 1 run function offroader:veh/tick_plugin
execute unless score #plugin offr.dummy matches 1 run function offroader:veh/tick_vanilla
