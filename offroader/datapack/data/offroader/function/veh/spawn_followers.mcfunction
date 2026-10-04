# Generat de gen_layout.py — nu edita manual.
# Toate entitățile-urmăritor ale vehiculului, invocate la poziția calului.
summon minecraft:item_display ~ ~ ~ {Tags:["offr_f","offr_body","offr_new_f"],item:{id:"minecraft:iron_ingot",count:1,components:{"minecraft:item_model":"offroader:body"}},item_display:"none",teleport_duration:1,interpolation_duration:1,view_range:1.5,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.4f,1.4f,1.4f]},shadow_radius:0f}
summon minecraft:item_display ~ ~ ~ {Tags:["offr_f","offr_swheel","offr_new_f"],item:{id:"minecraft:iron_ingot",count:1,components:{"minecraft:item_model":"offroader:swheel_car"}},item_display:"none",teleport_duration:1,interpolation_duration:1,view_range:1.5,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.4f,1.4f,1.4f]},shadow_radius:0f}
summon minecraft:item_display ~ ~ ~ {Tags:["offr_f","offr_w0","offr_new_f"],item:{id:"minecraft:iron_ingot",count:1,components:{"minecraft:item_model":"offroader:wheel"}},item_display:"none",teleport_duration:1,interpolation_duration:1,view_range:1.5,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.4f,1.4f,1.4f]},shadow_radius:0f}
summon minecraft:item_display ~ ~ ~ {Tags:["offr_f","offr_w1","offr_new_f"],item:{id:"minecraft:iron_ingot",count:1,components:{"minecraft:item_model":"offroader:wheel"}},item_display:"none",teleport_duration:1,interpolation_duration:1,view_range:1.5,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.4f,1.4f,1.4f]},shadow_radius:0f}
summon minecraft:item_display ~ ~ ~ {Tags:["offr_f","offr_w2","offr_new_f"],item:{id:"minecraft:iron_ingot",count:1,components:{"minecraft:item_model":"offroader:wheel"}},item_display:"none",teleport_duration:1,interpolation_duration:1,view_range:1.5,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.4f,1.4f,1.4f]},shadow_radius:0f}
summon minecraft:item_display ~ ~ ~ {Tags:["offr_f","offr_w3","offr_new_f"],item:{id:"minecraft:iron_ingot",count:1,components:{"minecraft:item_model":"offroader:wheel"}},item_display:"none",teleport_duration:1,interpolation_duration:1,view_range:1.5,transformation:{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[1.4f,1.4f,1.4f]},shadow_radius:0f}
summon minecraft:text_display ~ ~ ~ {Tags:["offr_f","offr_name","offr_new_f"],text:{text:"Offroader",color:"gold",bold:true,italic:false},billboard:"center",teleport_duration:1,view_range:0.4,shadow_radius:0f}
summon minecraft:armor_stand ~ ~ ~ {Tags:["offr_f","offr_s1","offr_new_f","offr_seat"],Marker:1b,Invisible:1b,Invulnerable:1b,NoGravity:1b,PersistenceRequired:1b}
summon minecraft:armor_stand ~ ~ ~ {Tags:["offr_f","offr_s2","offr_new_f","offr_seat"],Marker:1b,Invisible:1b,Invulnerable:1b,NoGravity:1b,PersistenceRequired:1b}
summon minecraft:armor_stand ~ ~ ~ {Tags:["offr_f","offr_s3","offr_new_f","offr_seat"],Marker:1b,Invisible:1b,Invulnerable:1b,NoGravity:1b,PersistenceRequired:1b}
summon minecraft:interaction ~ ~ ~ {Tags:["offr_f","offr_i0","offr_new_f","offr_i_driver"],width:1.0f,height:1.4f,response:1b}
summon minecraft:interaction ~ ~ ~ {Tags:["offr_f","offr_i1","offr_new_f","offr_i_seat"],width:0.9f,height:1.3f,response:1b}
summon minecraft:interaction ~ ~ ~ {Tags:["offr_f","offr_i2","offr_new_f","offr_i_seat"],width:0.9f,height:1.3f,response:1b}
summon minecraft:interaction ~ ~ ~ {Tags:["offr_f","offr_i3","offr_new_f","offr_i_seat"],width:0.9f,height:1.3f,response:1b}
# leagă urmăritorii de vehicul prin scorul offr.id
scoreboard players operation @e[tag=offr_new_f] offr.id = @s offr.id
# cache pentru timestamp-urile interaction-urilor (evită click fantomă la spawn)
scoreboard players set @e[tag=offr_new_f,type=minecraft:interaction] offr.ts 0
execute as @e[tag=offr_new_f,type=minecraft:interaction] store result score @s offr.ts run data get entity @s interaction.timestamp
tag @e[tag=offr_new_f] remove offr_new_f
