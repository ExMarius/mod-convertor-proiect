# Offroader 1:1 — vanilla datapack + resourcepack (Java 26.3)

Recreerea offroader-ului din **MrCrayfish's Vehicle Mod 0.45.2** pe un server
**NEMODDAT**, folosind **asset-urile reale ale modului** (model, texturi,
sunete), convertite automat în formate vanilla.

> ⚠️ **Doar pentru test personal.** Asset-urile din `resourcepack/` provin din
> modul MrCrayfish (licența lui se aplică) — nu redistribui pack-urile public.

## Ce e 1:1 cu modul

| Element | Sursă în mod | Cum ajunge în joc |
|---|---|---|
| Caroseria (163 cuburi) | `models/vehicle/off_roader_body.json` | model item vanilla, identic |
| Roțile (octagonale) | `models/item/off_road_wheel.json` | 4 item_display rotite individual |
| Volanul | `models/vehicle/go_kart_steering_wheel.json` | transformarea exactă a renderer-ului (rotX −45°, scara 0.75) în `display.none` |
| Texturile | `textures/model/*.png` + blocuri vanilla (beton alb, vată neagră, sticlă...) | copiate/referite direct |
| Sunet motor | `sounds/entity/jet_ski/engine.ogg` | pitch 0.8–1.6 exact ca în mod |
| Claxon | `sounds/entity/vehicle/horn.ogg` | idem |
| Gâlgâit alimentare | `sounds/item/jerrycan/liquid_glug.ogg` | idem |
| Poziții roți/scaune | `VehiclePropertiesGen.java` (offroader) | roți ±10/±14.5 u, 4 scaune, scară 1.4 |
| Cheia + bidonul | `models/item/{key,jerry_can}.json` | iteme vanilla cu model custom |

Comportament (cal invizibil = fizică): condus WASD, boost, combustibil 600
(≈10 min), bidon +20%, claxon, 4 locuri, direcția roților față după viraj.

## Instalare

1. **Server/lume 26.3**: `OffroaderDatapack.zip` → `world/datapacks/`
2. **Client**: `OffroaderResourcePack.zip` → `resourcepacks/` + activare
3. `/reload` → `/function offroader:give` → `/function offroader:selftest`

Ambele ZIP-uri: `offroader/release/`.

## Pipeline de generare

```
sources/                      ← zip-urile modului (de pe branch-ul main) — NU se commituie
offroader/scripts/
  convert_from_mod.py         ← modele+texturi+sunete din mod → resourcepack
  config.py                   ← geometria 1:1 (din VehiclePropertiesGen)
  gen_quats.py                ← tabele quaternioni (yaw 10°, spin 15°)
  gen_layout.py               ← follow/fl_* + spawn_followers (14 entități)
  gen_sounds.py               ← start/stop/boost (celelalte vin din mod)
  build_packs.py [--regen]    ← validează tot + face ZIP-urile
```

Refacere completă: `python3 scripts/build_packs.py --regen` (necesită
`sources/` extras — vezi `offroader/README.md`).

## Testare

- `/function offroader:selftest` — 18 verificări automate cu verdict în chat
- Ghid complet: `offroader/testserver/README.md`
