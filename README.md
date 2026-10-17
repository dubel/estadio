# Estadio da Gruz — Rekonstrukcja Historyczna 3D Stadionu ŁKS Łódź (1969–2012)

Trójwymiarowa rekonstrukcja architektoniczna oraz wirtualny spacer 3D (WebGL / Three.js) po nieistniejącym już, kultowym stadionie **ŁKS Łódź** przy **al. Unii Lubelskiej 2** w jego historycznym kształcie z lat 1969–2012.

Obiekt został zrekonstruowany w skali 1:1 w programie **Blender** przy użyciu automatycznych skryptów Python (`bpy`) oraz przeniesiony do interaktywnej aplikacji webowej w **Three.js** (Vite + TypeScript).

---

## 🏛️ Główne Elementy Architektoniczne

1. **Trybuna Główna (Zachodnia)**:
   - Konstrukcja żelbetowa późnego modernizmu/brutalizmu PRL z 14 potężnymi dźwigarami i zewnętrznymi ukośnymi odciągami.
   - Sektor górny: 26 rzędów z drewnianymi ławkami i przejściami schodowymi (nachylenie widowni $29^\circ$, wysokość korony $\approx 14\text{ m}$).
   - Sektor dolny: 10 rzędów widowni pod niskim blaszanym zadaszeniem VIP z frontową blendą fasadową niosącą historyczne hasło klubowe:
     `TUTAJ WYCHOWANI • ŁKS TO WIĘCEJ NIŻ KLUB • WIERNI I ODDANI`.
   - Tylna ściana pawilonu z pasmami okien wychodząca w stronę Parku na Zdrowiu i boisk treningowych.

2. **Maszty Oświetleniowe (Jupitery z 1970 r.)**:
   - 4 maszty kratownicowe o wysokości 46 m, każdy oparty na 3 rozszerzających się ku dołowi nogach.
   - Głowica w kształcie odwróconego krótszym bokiem trapezu (szerokość od 3.8 m do 7.4 m).
   - 45 reflektorów na każdym maszcie, pochylonych pod kątem $28^\circ$ w dół bezpośrednio w płytę boiska.

3. **Podkowa Ziemna i Galera (Wschód)**:
   - Trybuna wschodnia (**Galera**) biegnąca wzdłuż **al. Unii Lubelskiej** z historycznymi banerami kibicowskimi (`RODOWICI ŁODZIANIE`, `GALERA JEST TYLKO JEDNA`).
   - Podkowa trybun oparta na wałach ziemnych z 20 betonowymi stopniami.
   - Ciągła fosa betonowa (szerokość 1.8 m, głębokość 1.4 m) oddzielająca trybuny od bieżni.

4. **Tablica Wyników i Zegar Omega (Południe)**:
   - Zlokalizowana na koronie krótkiej trybuny od południa, skierowana frontem na północ ku murawie.
   - Duża ciemna tablica z okrągłą białą tarczą zegarową Omega / ŁKS z cyframi rzymskimi.

5. **Płyta Boiska i Bieżnia**:
   - Pełnowymiarowe boisko piłkarskie $105\text{ m} \times 68\text{ m}$ z fotorealistyczną murawą PBR (CC0 ambientCG) i 20 naprzemiennymi pasami koszenia.
   - Oficjalne kredowe oznaczenia PZPN / FIFA (linie, koło środkowe $R=9.15\text{ m}$, pola karne, łuki).
   - Bramki z siatkami i ławki rezerwowych.
   - 8-metrowa bieżnia lekkoatletyczna okalająca murawę, mieszcząca się w całości przed trybunami.

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
- **[1]–[7]:** Teleportacja do kluczowych sektorów:
  - `1` — Środek Murawy
  - `2` — Korona Trybuny Głównej (Rząd 26)
  - `3` — Loża VIP
  - `4` — Zegar (Łuk Południowy)
  - `5` — Galera (Al. Unii Lubelskiej)
  - `6` — Jupiter NW
  - `7` — Bramka Południowa
- **[L]:** Przełączanie oświetlenia Dzień / Noc (włączenie jupiterów).
- **[V]:** Przełączanie trybu: Spacer (widok FPV z kolizjami, grawitacją i wchodzeniem po stopniach do 48 cm) / Dron (lot swobodny).
- **Mysz + WASD + Shift:** Rozglądanie po kliknięciu w canvas, poruszanie się, sprint.
- **Spacja:** skok (Spacer, ok. 0.5 m) / wznoszenie (Dron). **[C]:** opadanie (Dron).

### Test fizyki

```bash
npm run test:physics
```

Uruchamia Vite i headless Chrome, sprawdza grawitację, wysokość skoku oraz schodzenie i wchodzenie po stopniach trybuny głównej i Galery.

---

## 🛠️ Rekonstrukcja w Blenderze (CLI)

Wszystkie elementy stadionu generowane są w pełni parametrycznie przez skrypty w katalogu `tools/`:

```bash
# 1. Złożenie pełnego modelu stadionu i eksport do GLB
blender -b --python tools/build_full_stadium.py

# 2. Wyrenderowanie 4 ujęć kinematograficznych
blender -b --python tools/render_stadium_cinematic.py
```

Wygenerowany model:
- `stadion_lks_pelny.blend` (scena źródłowa Blendera)
- `public/assets/estadio_da_gruz.glb` (model GLTF ze spakowanymi teksturami PBR do Three.js)

Tekstury źródłowe (wejście Blendera i `tools/generate_stadium_textures.py`) leżą w `assets/textures/`.
Do aplikacji trafiają wyłącznie spakowane w GLB — w `public/assets/textures/` potrzebny jest tylko `floodlight_glow.png` (sprite ładowany przez `src/main.ts`).
