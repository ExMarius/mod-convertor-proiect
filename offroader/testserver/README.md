# Cum testăm offroader-ul

Sandbox-ul în care lucrez eu nu poate accesa serverele Mojang (doar GitHub/PyPI),
deci **serverul de Minecraft îl pornești tu** — dar am făcut totul cât mai simplu:

1. **Selftest integrat** — o singură comandă în joc testează automat tot datapack-ul
   și îți afișează `[OK]/[ESEC]` pe fiecare funcționalitate. Îmi trimiși lista
   (screenshot/copiere) și corectez orice e roșu.
2. **Script de setup** — îți pregătește serverul oficial 1.21.4 cu 2 comenzi.

---

## Varianta A — Single-player (cel mai rapid, 2 minute)

1. Minecraft Launcher → profil **1.21.4** → creează o lume nouă (Cheats: ACTIVATE,
   tip: Flat/Supraplă — mai ușor de testat).
2. Copiază `offroader/release/OffroaderDatapack.zip` în:
   - Windows: `%appdata%\.minecraft\saves\<lumea>\datapacks\`
   - Linux: `~/.minecraft/saves/<lumea>/datapacks/`
   (creează folderul `datapacks` dacă nu există)
3. Copiază `offroader/release/OffroaderResourcePack.zip` în `.minecraft/resourcepacks/`
   și activează-l din Setări → Pachete de resurse.
4. În joc: `/reload`, apoi:
   ```
   /function offroader:give
   /function offroader:selftest
   ```

## Varianta B — Server dedicat local (ca pe serverul „adevărat")

### Cu scriptul meu (recomandat; necesită Python 3)

```bash
cd mod-convertor-proiect
python3 offroader/testserver/setup_server.py 1.21.4
cd ~/.cache/mc-server
./java/bin/java -Xms512M -Xmx2G -jar server.jar nogui
```

Scriptul: descarcă **server.jar oficial** de la Mojang (cu verificare SHA1),
**JRE-ul** necesar (Temurin), scrie `eula.txt` + `server.properties`
(lume flat, RCON activ pe portul 25575 cu parola `offr-test`) și instalează
datapack-ul în `world/datapacks/`.

Pe Windows: instalează Python de la python.org, apoi_rulează la fel în cmd
(căile `.cache` se fac în `%userprofile%`).

### Manual (fără Python)

1. Descarcă `server.jar` de la [minecraft.net/download/server](https://www.minecraft.net/download/server)
   (versiunea **1.21.4**) într-un folder nou.
2. Ai nevoie de Java (versiunea cerată de 1.21.4; dacă lipsește: [adoptium.net](https://adoptium.net)).
3. În folder: `java -Xms512M -Xmx2G -jar server.jar nogui` → se oprește cu eroare EULA.
4. Editează `eula.txt`: `eula=true`. Rulează din nou — apare lumea.
5. Copiază `OffroaderDatapack.zip` în `world/datapacks/` (creează folderul).
6. Conectează-te cu clientul 1.21.4 la `localhost`, instalează resource pack-ul client-side.

---

## Testul automat (pas cu pas)

În joc, ca jucător cu op (single-player: tu; server: `/op Nume`):

```
/function offroader:give        # primești cheia, volanul, bidonul
/function offroader:selftest    # testul complet, ~5 secunde
```

**ATENȚIE:** selftest-ul șterge vehiculele offroader aflate în 24 de blocuri —
rulează-l departe de alte mașini.

Ce verifică automat (18 puncte): invocarea vehiculului, cei 13 urmăritori
(caroserie/roți/nume/scaune/hitbox-uri), modelul custom, pornirea motorului
(viteza croazieră), boost-ul (viteza 0.55), rotile care se învârt, urmărirea
mașinii în mișcare, alimentarea (+40), claxonul, parcarea, cele 3 iteme,
depozitarea și curățenia după.

La final afișează `X trecute, Y esuate` — **trimite-mi toată lista**.

## Testul manual (ce nu poate verifica funcțiile)

- [ ] Modelul arată bine (caroserie olive, bare negre, 4 roți) — necesită resource pack activ
- [ ] Șoferul stă natural pe scaunul din față (nu plutește, nu e în capotă)
- [ ] Sunete: pornire, motor care urcă cu viteza, claxon, boost, gâlgâit
- [ ] WASD conduce natural; spațiu sare obstacole de 1 bloc
- [ ] Click pe scaunele din spate te urcă pasager
- [ ] Icoanele itemelor (cheie aurie, volan, bidon roșu) în inventar
- [ ] HUD km/h + combustibil pe bara de acțiune în timp ce șofezi
- [ ] Volanul din mână + click-dreapta = boost (cu cooldown 30 s)

Dacă ceva e dezactivat/strâmb, fă un screenshot (F2) și spune-mi ce vezi —
regenerez pachetul cu corecțiile în câteva minute.

## Server cu prieteni (opțional)

- **LAN**: din single-player → Esc → „Open to LAN".
- **Hosting gratuit** (Aternos etc.): caută versiunea 1.21.4 (e nouă, s-ar săgeta
  aparate câteva zile); încarcă `OffroaderDatapack.zip` ca datapack.
- **VPS/port forwarding**: portul 25565 TCP; fiecare jucător instalează
  resource pack-ul client-side.
