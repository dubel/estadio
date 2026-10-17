# Estadio da Gruz — Rekonstrukcja Historyczna 3D Stadionu ŁKS Łódź (1969–2012)

Trójwymiarowa rekonstrukcja architektoniczna oraz wirtualny spacer 3D (WebGL / Three.js) po nieistniejącym już, kultowym stadionie **ŁKS Łódź** przy **al. Unii Lubelskiej 2** w jego historycznym kształcie z lat 1969–2012.

Obiekt został zrekonstruowany w skali 1:1 w programie **Blender** przy użyciu automatycznych skryptów Python (`bpy`) oraz przeniesiony do interaktywnej aplikacji webowej w **Three.js** (Vite + TypeScript).

---

## 🏛️ Główne Elementy Architektoniczne

1. **Trybuna Główna (Zachodnia)**:
   - Konstrukcja żelbetowa późnego modernizmu/brutalizmu PRL (proj. J. Wyżnikiewicz, 1969): 14 przęseł po ~9,3 m (ok. 130 m długości) i zewnętrzne ukośne odciągi.
   - Przekrój wg rysunku projektowego: sektor górny 33 rzędy ławek (malowane drewno w kolorze kości słoniowej), korona ok. 18,4 m nad terenem, bez dachu; biała balustrada czołowa z Przeplatanką ŁKS.
   - Sektor dolny: 10 rzędów plastikowych krzesełek pod daszkiem (biały–czerwony–biały), za nim promenada na wysokości 3,2 m.
   - Tunel w każdym z 14 przęseł: schody z hali pod trybuną wyprowadzają na 7. rząd sektora górnego. Poniżej wyjść, 4–5 rzędów nad daszkiem, stoją bloczki z Przeplatanką. Przejścia mają żółte poręcze.
   - Ławki rezerwowych z mlecznej pleksi wpuszczone w sektor dolny.
   - Z tyłu (od zachodu, strona Atlas Areny) podwieszony budynek ze wstęgą okien.

2. **Maszty Oświetleniowe (Jupitery z 1970 r.)**:
   - 4 maszty kratownicowe o wysokości 46 m. Poniżej 15 m trzon rozchodzi się na 3 nogi zakotwione w betonowych blokach. W połowie wysokości jest pomost z dodatkowymi reflektorami.
   - Głowica w kształcie odwróconego krótszym bokiem trapezu (szerokość od 3.8 m do 7.4 m).
   - 45 reflektorów na każdym maszcie, pochylonych pod kątem $28^\circ$ w dół bezpośrednio w płytę boiska.

3. **Podkowa Ziemna i Galera (Wschód)**:
   - Trybuna wschodnia (**Galera**) biegnąca wzdłuż **al. Unii Lubelskiej** z historycznymi banerami kibicowskimi (`RODOWICI ŁODZIANIE`, `GALERA JEST TYLKO JEDNA`).
   - Podkowa trybun oparta na wałach ziemnych z 20 betonowymi stopniami.
   - Bez muru oporowego: rzędy kończą się ok. 1,5 m przed ogrodzeniem na gruncie. Przed Galerą i między jej sekcjami stoi stalowe ogrodzenie (pełne panele u dołu, siatka wyżej), na łukach niskie z biało-czerwonymi słupkami. Północny kraniec boiska zamyka ogrodzenie z blachy trapezowej (za nim trawa przed łukiem).
   - Galera ma 6 sekcji kolorystycznych krzesełek: czerwoną, cztery biało-czerwono-białe (w jednej pikselowy napis ŁKS) i sekcję z czerwonym pasem u góry i gołym betonem z żółtymi barierkami.
   - Czerwone plastikowe krzesełka na prostej Galery.
   - Dwa duże tunele wejściowe Galery przy styku z łukami: wcięcie o przekroju trapezu w 10 pierwszych rzędów, w jego głębi wylot przelotu pod wałem z Przeplatanką na nadprożu.

4. **Tablica Wyników i Zegar Omega (Południe)**:
   - Zlokalizowana na koronie krótkiej trybuny od południa, skierowana frontem na północ ku murawie.
   - Duża ciemna tablica z okrągłą białą tarczą zegarową Omega / ŁKS z cyframi rzymskimi.

5. **Płyta Boiska**:
   - Pełnowymiarowe boisko piłkarskie $105\text{ m} \times 68\text{ m}$ z fotorealistyczną murawą PBR (CC0 ambientCG) i 20 naprzemiennymi pasami koszenia.
   - Oficjalne kredowe oznaczenia PZPN / FIFA (linie, koło środkowe $R=9.15\text{ m}$, pola karne, łuki).
   - Bramki z siatkami.
   - Pas dawnej bieżni (8 m) porośnięty trawą aż do ogrodzenia: model pokazuje stan z lat 2010–2012.

6. **Otoczenie (stan z ortofotomapy 2013)**: teren i plac wokół stadionu, al. Unii Lubelskiej, tory przy Łodzi Kaliskiej, Atlas Arena, 96 drzew (EZ-Tree) oraz panorama bloków za torami, widoczna z trybuny głównej nad Galerą.

Wymiary, kalibracja ortofotomapy, mapa zdjęć archiwalnych i otwarte pytania: [`docs/zrodla.md`](docs/zrodla.md).

---

## 🚀 Uruchomienie Wirtualnego Spaceru (Three.js)

```bash
# Instalacja zależności
npm install

# Uruchomienie serwera deweloperskiego
npm run dev
```

Aplikacja uruchomi się pod adresem: `http://localhost:3000/`.

### Sterowanie:
- **[1]–[8]:** Teleportacja do kluczowych sektorów:
  - `1` — Środek Murawy
  - `2` — Korona Trybuny Głównej (Rząd 33)
  - `3` — Loża VIP
  - `4` — Zegar (Łuk Południowy)
  - `5` — Galera (Al. Unii Lubelskiej)
  - `6` — Jupiter NW
  - `7` — Bramka Południowa
  - `8` — Tunel pod Trybuną Główną (schody na widownię)
- **[L]:** Przełączanie oświetlenia Dzień / Noc (włączenie jupiterów).
- **[V]:** Przełączanie trybu: Spacer (widok FPV z kolizjami, grawitacją i wchodzeniem po stopniach do 48 cm) / Dron (lot swobodny).
- **Mysz + WASD + Shift:** Rozglądanie po kliknięciu w canvas, poruszanie się, sprint.
- **Spacja:** skok (Spacer, ok. 0.5 m) / wznoszenie (Dron). **[C]:** opadanie (Dron).

### Test fizyki

```bash
npm run test:physics
```

Uruchamia Vite i headless Chrome, sprawdza grawitację, wysokość skoku, schodzenie i wchodzenie po stopniach trybuny głównej i Galery, schody tunelu (także poza osią), przejście tunelem Galery, ogrodzenie oraz teren za stadionem.

---

## 🌥️ Oświetlenie

Pochmurne popołudnie (17.09.2011, 16:00): słońce liczone z położenia Łodzi i obrotu osi stadionu (`src/lighting.ts`),
światło otoczenia z HDRI [Overcast Soil (Pure Sky)](https://polyhaven.com/a/overcast_soil_puresky), Poly Haven, CC0
(`public/assets/env/`), AO wypalone w Blenderze dla betonu i placu, ziarno i mapowanie tonów (`src/postfx.ts`).
Noc: jupitery, smugi światła, bloom.

## 🛠️ Rekonstrukcja w Blenderze (CLI)

Wszystkie elementy stadionu generowane są w pełni parametrycznie przez skrypty w katalogu `tools/`:

```bash
# 1. Złożenie modelu, wypalenie AO (Cycles, ~2 min) i kompresja (meshopt + WebP)
npm run model:build
#    BAKE_AO=0 npm run model:build   — szybki build bez wypalania AO

# 2. Wyrenderowanie ujęć kinematograficznych
blender -b --python tools/render_stadium_cinematic.py
```

Wygenerowany model:
- `stadion_lks_pelny.blend` (scena źródłowa Blendera)
- `build/estadio_da_gruz.raw.glb` i `build/ao/` (surowy eksport i wypalone mapy AO, poza gitem)
- `public/assets/estadio_da_gruz.glb` (model skompresowany do Three.js, ok. 5 MB)

Tekstury źródłowe (wejście Blendera i `tools/generate_stadium_textures.py`) leżą w `assets/textures/`.

Pomocnicze:
- `python3 tools/extract_trees_from_ortho.py`: pozycje drzew z ortofotomapy (`tools/data/drzewa_ortofoto.json`).
- `npm run trees:build`: drzewa generowane przez [EZ-Tree](https://github.com/dgreenheck/ez-tree) (MIT; kora z Poly Haven i TextureCan, CC0) w headless Chrome (`tools/generate_trees.mjs`, odmiany w `tools/trees/generate.js`): brzoza, topola, jesion, dąb na pozycjach z ortofotomapy, instancje w `public/assets/drzewa.glb`. Pnie do kolizji są w modelu stadionu (`Drzewa_Pnie_Kolizje`, niewidoczne).
- `blender stadion_lks_pelny.blend --python tools/add_ortho_reference.py`: ortofotomapa jako podkład 1:1 do modelowania „po śladzie”.

Do aplikacji trafiają wyłącznie spakowane w GLB — w `public/assets/textures/` potrzebny jest tylko `floodlight_glow.png` (sprite ładowany przez `src/main.ts`).
