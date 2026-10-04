"""
Generează funcțiile de layout ale vehiculului (o singură sursă de adevăr:
config.FOLLOWERS):
  - veh/follow.mcfunction        (dispatcherul per tick, chemat din veh/tick)
  - veh/fl_<tag>.mcfunction      (poziționare per follower + yaw/spin)
  - veh/spawn_followers.mcfunction (summon-urile la spawn)

Rulare: python3 gen_layout.py
"""
import os
import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
FUNC = os.path.join(HERE, "..", "datapack", "data", C.NS, "function", "veh")

SCALE = C.DISPLAY_SCALE


def fnum(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def tp_line(pos):
    x, y, z = pos
    return f"tp @s ^{fnum(x)} ^{fnum(y)} ^{fnum(z)}"


TRANSFORM = ("transformation:{left_rotation:[0f,0f,0f,1f],"
             "right_rotation:[0f,0f,0f,1f],"
             "translation:[0f,0f,0f],"
             f"scale:[{SCALE}f,{SCALE}f,{SCALE}f]}}")


def summon_line(tag, kind, model, pos, extra):
    tags = ["offr_f", tag, "offr_new_f"]
    if kind == "item_display":
        tags_str = ",".join(f'"{t}"' for t in tags)
        return (f'summon minecraft:item_display ~ ~ ~ {{Tags:[{tags_str}],'
                f'item:{{id:"minecraft:iron_ingot",count:1,'
                f'components:{{"minecraft:item_model":"{model}"}}}},'
                f'item_display:"none",teleport_duration:1,'
                f'interpolation_duration:1,view_range:1.5,'
                f'{TRANSFORM},shadow_radius:0f}}')
    if kind == "text_display":
        tags_str = ",".join(f'"{t}"' for t in tags)
        return (f'summon minecraft:text_display ~ ~ ~ {{Tags:[{tags_str}],'
                f'text:{{text:"Offroader",color:"gold",bold:true,italic:false}},'
                f'billboard:"center",teleport_duration:1,view_range:0.4,'
                f'shadow_radius:0f}}')
    if kind == "armor_stand":
        tags.append("offr_seat")
        tags_str = ",".join(f'"{t}"' for t in tags)
        return (f'summon minecraft:armor_stand ~ ~ ~ {{Tags:[{tags_str}],'
                f'Marker:1b,Invisible:1b,Invulnerable:1b,NoGravity:1b,'
                f'Persistent:1b}}')
    if kind == "interaction":
        if extra.get("role") == "driver":
            tags.append("offr_i_driver")
        else:
            tags.append("offr_i_seat")
        tags_str = ",".join(f'"{t}"' for t in tags)
        return (f'summon minecraft:interaction ~ ~ ~ {{Tags:[{tags_str}],'
                f'width:{extra["w"]}f,height:{extra["h"]}f,response:1b}}')
    raise SystemExit(f"tip necunoscut: {kind}")


def main():
    os.makedirs(FUNC, exist_ok=True)

    # ---- fl_<tag>.mcfunction ----
    for tag, kind, model, pos, extra in C.FOLLOWERS:
        lines = []
        if kind == "text_display":
            lines.append("# Generat de gen_layout.py — nu edita manual.")
            lines.append(tp_line(pos))
        else:
            lines.append("# Generat de gen_layout.py — nu edita manual.")
            lines.append(tp_line(pos))
            if extra.get("yaw"):
                lines.append("function offroader:veh/set_yaw with storage offroader:call")
            if extra.get("spin"):
                lines.append("function offroader:veh/set_spin with storage offroader:call")
        with open(os.path.join(FUNC, f"fl_{tag}.mcfunction"), "w") as f:
            f.write("\n".join(lines) + "\n")

    # ---- spawn_followers.mcfunction (rulează as/at calul) ----
    L = ["# Generat de gen_layout.py — nu edita manual.",
         "# Toate entitățile-urmăritor ale vehiculului, invocate la poziția calului."]
    for tag, kind, model, pos, extra in C.FOLLOWERS:
        role = extra.get("role")
        ex = dict(extra)
        if kind == "interaction":
            ex["role"] = role or ("driver" if tag == "offr_i0" else "seat")
        L.append(summon_line(tag, kind, model, pos, ex))
    L += [
        "# leagă urmăritorii de vehicul prin scorul offr.id",
        "scoreboard players operation @e[tag=offr_new_f] offr.id = @s offr.id",
        "# cache pentru timestamp-urile interaction-urilor (evită click fantomă la spawn)",
        "scoreboard players set @e[tag=offr_new_f,type=minecraft:interaction] offr.ts 0",
        "execute as @e[tag=offr_new_f,type=minecraft:interaction] store result score @s offr.ts run data get entity @s interaction.timestamp",
        "tag @e[tag=offr_new_f] remove offr_new_f",
    ]
    with open(os.path.join(FUNC, "spawn_followers.mcfunction"), "w") as f:
        f.write("\n".join(L) + "\n")

    # ---- follow.mcfunction (rulează as/at calul, în fiecare tick) ----
    F = ["# Generat de gen_layout.py — nu edita manual.",
         "# 1) indicii de rotire (yaw caroserie + unghi roți) în storage pt macro-uri",
         "scoreboard players operation #cur offr.tmp = @s offr.id",
         "execute store result score #yaw offr.tmp run data get entity @s Rotation[0] 1",
         "scoreboard players operation #yaw offr.tmp += #c180 offr.dummy",
         "scoreboard players operation #yaw offr.tmp %= #c360 offr.dummy",
         "scoreboard players operation #yaw offr.tmp /= #c10 offr.dummy",
         "execute if score #yaw offr.tmp matches 36.. run scoreboard players set #yaw offr.tmp 0",
         "execute if score #flip offr.dummy matches 1.. run scoreboard players add #yaw offr.tmp 18",
         "execute if score #yaw offr.tmp matches 36.. run scoreboard players set #yaw offr.tmp 0",
         "scoreboard players operation #widx offr.tmp = @s offr.wheel",
         "execute if score #spinflip offr.dummy matches 1.. run scoreboard players operation #widx offr.tmp *= #n1 offr.dummy",
         "execute if score #spinflip offr.dummy matches 1.. run scoreboard players add #widx offr.tmp 24",
         "execute if score #widx offr.tmp matches 24.. run scoreboard players set #widx offr.tmp 0",
         "execute store result storage offroader:call y int 1 run scoreboard players get #yaw offr.tmp",
         "execute store result storage offroader:call w int 1 run scoreboard players get #widx offr.tmp",
         "# 2) poziționează fiecare urmăritor (offseturi locale față de cal)",
         ]
    for tag, kind, model, pos, extra in C.FOLLOWERS:
        F.append(f"execute at @s as @e[tag={tag},distance=..6] "
                 f"if score @s offr.id = #cur offr.tmp run function offroader:veh/fl_{tag}")
    F += [
        "# 3) verifică click-urile pe scaune (interaction entities)",
        "execute at @s as @e[tag=offr_i_driver,distance=..6] if score @s offr.id = #cur offr.tmp run function offroader:veh/check_driver_i",
        "execute at @s as @e[tag=offr_i_seat,distance=..6] if score @s offr.id = #cur offr.tmp run function offroader:veh/check_seat_i",
    ]
    with open(os.path.join(FUNC, "follow.mcfunction"), "w") as f:
        f.write("\n".join(F) + "\n")

    print("generate:", ", ".join(f"fl_{t[0]}" for t in C.FOLLOWERS))
    print("generate: follow.mcfunction, spawn_followers.mcfunction")


if __name__ == "__main__":
    main()
