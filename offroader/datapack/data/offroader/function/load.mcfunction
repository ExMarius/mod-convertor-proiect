# ============================================================
# Offroader — recreere vanilla a offroader-ului din MrCrayfish's
# Vehicle Mod. Țintă: Minecraft Java 26.3 (datapack format 121).
# ============================================================

# --- obiecte scoreboard ---
scoreboard objectives add offr.dummy dummy
scoreboard objectives add offr.tmp dummy
scoreboard objectives add offr.id dummy
scoreboard objectives add offr.fuel dummy
scoreboard objectives add offr.boost dummy
scoreboard objectives add offr.speed2 dummy
scoreboard objectives add offr.wheel dummy
scoreboard objectives add offr.ticks dummy
scoreboard objectives add offr.mode dummy
scoreboard objectives add offr.applied dummy
scoreboard objectives add offr.wasdriven dummy
scoreboard objectives add offr.ts dummy
scoreboard objectives add offr.horncd dummy
scoreboard objectives add offr.steer dummy
scoreboard objectives add offr.yaw dummy
scoreboard objectives add offr.yaw0 dummy
scoreboard objectives add offr.x dummy
scoreboard objectives add offr.z dummy
scoreboard objectives add offr.x0 dummy
scoreboard objectives add offr.z0 dummy
scoreboard objectives add offr.key minecraft.used:minecraft.warped_fungus_on_a_stick
scoreboard objectives add offr.throttle minecraft.used:minecraft.carrot_on_a_stick
scoreboard objectives add offr.can minecraft.used:minecraft.fishing_rod

# --- constante (nu reseta la /reload ce e deja setat) ---
scoreboard players set #c5 offr.dummy 5
scoreboard players set #c10 offr.dummy 10
scoreboard players set #c100 offr.dummy 100
scoreboard players set #c360 offr.dummy 360
scoreboard players set #c900 offr.dummy 900
scoreboard players set #c3 offr.dummy 3
scoreboard players set #c6 offr.dummy 6
scoreboard players set #c16 offr.dummy 16
scoreboard players set #c500 offr.dummy 500
scoreboard players set #c800 offr.dummy 800
scoreboard players set #c1600 offr.dummy 1600
scoreboard players set #c18000 offr.dummy 18000
scoreboard players set #c36000 offr.dummy 36000
scoreboard players set #n1 offr.dummy -1
execute unless score #nextid offr.id = #nextid offr.id run scoreboard players set #nextid offr.id 0
execute unless score #flip offr.dummy = #flip offr.dummy run scoreboard players set #flip offr.dummy 0
execute unless score #spinflip offr.dummy = #spinflip offr.dummy run scoreboard players set #spinflip offr.dummy 0

# --- tabelele de quaternioni pentru rotiri ---
function offroader:veh/init_quats

tellraw @a {text:"[Offroader] Datapack încărcat! Obiecte: /function offroader:give",color:"gold"}
