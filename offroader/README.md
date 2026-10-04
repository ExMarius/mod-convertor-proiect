# Offroader — pachete vanilla (detalii tehnice)

Două pachete independente:

- **`datapack/`** → `release/OffroaderDatapack.zip` — logica vehiculului.
- **`resourcepack/`** → `release/OffroaderResourcePack.zip` — modelul, itemele, sunetele.

Ținta: **Minecraft Java 1.21.4** (datapack format 61 / resource pack format 46).

## Arhitectură

```
mașina = cal invizibil (fizica mersului)
       + 13 „followers" teleportați deasupra lui în fiecare tick:
         • 1 item_display  — caroseria (body.json, 52 cuburi)
         • 4 item_display  — roțile (wheel.json), rotite individual
         • 1 text_display  — numele mașinii
         • 3 armor_stand   — „scaune" (mount-points pentru pasageri)
         • 4 interaction   — hitbox-uri de click (șofer + 3 pasageri)
```

- Fiecare vehicul are un `offr.id` unic (scoreboard) — suportă mașini multiple.
- Fiecare tick, `veh/tick` → `veh/driving`/`veh/parked` → `veh/follow`
  repoziționează toți follower-ii relativ la cal (coordonate locale `^dx ^dy ^dz`),
  aplică yaw-ul caroseriei și spinul roților din tabelele de quaternioni
  (`veh/init_quats` în data storage) prin macrouri (`veh/set_yaw`, `veh/set_spin`).
- Viteza reală se măsoară cu `Pos` pe două tick-uri consecutive (`speed2`),
  folosită pentru pitch-ul motorului, consum și HUD.

## Funcțiile datapack-ului

| Funcție | Rol |
|---|---|
| `load` / `tick` | inițializare (storage, obiecte) / bucla principală |
| `give` | dă cele 3 iteme (cheie, volan, bidon) |
| `item_use/key` | folosește cheia: claxon / spawn / store |
| `item_use/throttle` | folosește volanul: boost |
| `item_use/jerrycan` | folosește bidonul: reumplere + gâlgâit |
| `veh/spawn`, `veh/store`, `veh/store_do` | invocă/strânge vehiculul |
| `veh/driving`, `veh/parked`, `veh/apply_mode` | stare mers/parcare, viteza calului |
| `veh/engine`, `veh/engine_play` | sunetul de motor cu pitch după viteză |
| `veh/hud`, `veh/hud_ok`, `veh/hud_low` | HUD action-bar (km/h, combustibil) |
| `veh/horn`, `veh/boost`, `veh/refuel` | claxon, boost, reumplere |
| `veh/board_driver`, `veh/board_pass`, `veh/check_*_i` | urcarea în mașină |
| `selftest/*` | test automat: `/function offroader:selftest` — 18 verificări, verdict în chat |
| `veh/follow`, `veh/fl_*`, `veh/set_yaw`, `veh/set_spin`, `veh/init_quats`, `veh/spawn_followers` | GENERATE — nu edita manual |

## Calibrare

Toate constantele „umane" sunt în `scripts/config.py`:

- `DISPLAY_SCALE` — mărimea modelului (1.5 = ~4,4 blocuri lungime).
- `FOLLOWERS` — pozițiile roților/scaunelor/numelor față de cal
  (tuple `(dx, dy, dz)` în blocuri; `^+x` = stânga calului).
- Formulele de consum / praguri HUD / viteza maximă sunt în
  `datapack/data/offroader/function/veh/*.mcfunction` (comentate în română).

După orice modificare în `scripts/` rulează din folderul `scripts/`:

```
python3 build_packs.py --regen
```

Validarea include: echilibrul acoladelor din `.mcfunction`, existența tuturor
funcțiilor referențiate, JSON-uri valide, texturi și sunete prezente.

## Sunete

Generate sintetic (`gen_sounds.py`) ca OGG Vorbis **mono** 44,1 kHz (mono e
obligatoriu pentru poziționare 3D în Minecraft):

| Fișier | Descriere |
|---|---|
| `engine.ogg` | buclă 1,2 s — saw 65/70 Hz + sub 32,5 Hz + LFO 12,5 Hz (burble V8); se repeta la 1 s cu pitch 0,9–1,6 după viteză |
| `start.ogg` | compresie (8 pulsuri) + prinderea motorului |
| `stop.ogg` | cădere turație + pocnitură finală |
| `horn.ogg` | dual-ton 370/466 Hz, timbre „pătrat" |
| `boost.ogg` | sweep 85→230 Hz + suflu filtrat |
| `slosh.ogg` | 3 „gulps" cu zgomot treacă-bandă |

## Depanare în joc

- **Mașina e invizibilă** → resource pack-ul nu e activat client-side.
- **Nu pot urca** → click-dreapta direct pe zona scaunului (nu pe capotă);
  hitbox-urile sunt la nivelul scaunelor.
- **Mașina a dispărut** (cal ucis de comenzi/lavă) → follower-ii se curăță
  singuri în 1 s; spawnează alta cu cheia.
- **Mașina s-a răsturnat vizual** (ex. plugin de fizică) → `/kill @e[tag=offr_f]`
  și re-spawn cu cheia.
- **Reset complet**: `/function offroader:load` reîncarcă storage-ul (păstrează
  mașinile); ștergerea mașinilor: `/kill @e[tag=offr_f]` + `/kill @e[tag=offr_veh]`.
