# Verificare numerică poziții (rulează CA și LA cal):
# - roata w0 trebuie să fie la ~1.54 blocuri (dx²+dz² ≈ 239 cm²)
# - caroseria la ~0.35 blocuri deasupra calului
execute store result score #hx offr.tmp run data get entity @s Pos[0] 100
execute store result score #hz offr.tmp run data get entity @s Pos[2] 100
execute store result score #hy offr.tmp run data get entity @s Pos[1] 100
execute as @e[tag=offr_w0,limit=1,sort=nearest] run function offroader:selftest/wpos2
execute as @e[tag=offr_body,limit=1,sort=nearest] run function offroader:selftest/wpos3
