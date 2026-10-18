# Źródła i pomiary rekonstrukcji

Każdy wymiar modelu powinien wynikać z jednego ze źródeł poniżej. Przy zmianie geometrii dopisz, na czym się opiera.

## Układ współrzędnych

Układ stadionu (Blender): **X: wschód** (oś poprzeczna boiska), **Y: północ** (oś długa), metry, początek w środku boiska.
W Three.js (eksport Y-up): `x = X`, `y = wysokość`, `z = −Y`.

W rzeczywistości oś długa stadionu jest odchylona od północy geograficznej o **24,9° na zachód** (kierunek NNW–SSE).
Model trzyma oś stadionu wzdłuż osi współrzędnych, więc ten kąt trzeba uwzględnić przy pozycji słońca (Faza 2).

## Kalibracja ortofotomapy

Plik: `zdjecia/ortofotomapa2013.png` (1432 × 1226 px). Stała kalibracji: `tools/ortho_calibration.py`.

| Wielkość | Wartość | Jak wyznaczona |
|---|---|---|
| Kąt osi stadionu | 24,92° na zachód od N | PCA maski zielonej płyty (centroid 605,3 / 597,0 px) |
| Skala | 0,2675 m/px | linie bramkowe 392 px ↔ 105 m, szerokość pola karnego 155 px ↔ 40,32 m |
| Środek boiska | piksel (604,5; 584,8) obrazu obróconego | środek między liniami bramkowymi; korekta +2,4 m z symetrii masztów wschodnich |

Kontrola: nakładka modelu na ortofotomapę (`blender stadion_lks_pelny.blend --python tools/add_ortho_reference.py`).
Linie boiska modelu pokrywają się z liniami widocznymi na zdjęciu. Dokładność pomiarów ok. ±2–3 m.

## Pomiary i stan modelu

| Element | Źródło | Pomiar | W modelu | Pewność |
|---|---|---|---|---|
| Trybuna główna: długość | ortofotomapa | ok. 130 m; rozstaw dźwigarów 9,4 m (autokorelacja); 14 przęseł | 130 m, 14 × 9,29 m | wysoka |
| Trybuna główna: położenie | ortofotomapa (nakładka) | czoło daszku X ≈ −44,7 m; środek ~3 m na N od osi boiska | czoło −45 m, środek Y = +3 m | średnia |
| Trybuna główna: głębokość | przekrój Wyżnikiewicza + ortofotomapa | 41,7 m (przekrój), 39–44 m (orto) | 41,55 m (z budynkiem tylnym) | wysoka |
| Trybuna główna: przekrój | przekrój Wyżnikiewicza (skala 0–10 m) | patrz niżej | 10 + 33 rzędy, korona 18,4 m (stałe w `build_grandstand.py`) | wysoka |
| Tunele (vomitoria) | widok_na_trybune_z_sektora_gosci.png, detale_trybuny_zachodniej.png | tunel w każdym przęśle, żółte obrzeża ścian | 14 tuneli w osiach przęseł, wyjście na rząd 7 sektora górnego; przebieg schodów w hali to założenie | średnia |
| Mural i graffiti bloczków | grafy_na_trybunie.png, il20250305_898037523/543/559, lawka_rezerwowych.jpg, trybuna_vip.jpg | mural na balustradzie czołowej nad północną częścią; graffiti dzielnic na 13 bloczkach (od północy: WRWG, OS. KOPERNIKA, TOLECHÓW, POLESIE, STARE ŁK, ŁODZIANIE, RODOWICI, DĄBROWA, LEGION, SOJTA/ELKSA, JULIANÓW, RADOGOSZCZ, MARYSIN) | mural Y lokalne 4,6–39,9 m; bloczki poszerzone do 7,6 m (od tunelu do tunelu, przerwa na przejście w osi przęsła), wys. 1,25 m; atlas `graffiti_bloczki.png` (`generate_block_graffiti_atlas`) | średnia (kolejność sąsiadów ze zdjęć pewna, przypisanie do konkretnych osi przybliżone) |
| Pawilon VIP | grafy_na_trybunie.png, widok_na_trybune_z_sektora_gosci.png | bryła z blachy ocynkowanej na tylnych rzędach sektora dolnego, wstęga okien od boiska; przed nim 3 rzędy krzesełek | Y lokalne 5,0–37,1 m (do białego daszku), od 4. rzędu do końca rzędów (promenada za nim wolna), wys. 4,4 m, okna 2,4–3,6 m | niska (wysokość, okna, zasięg na północ) |
| Trybuna tymczasowa i piłkochwyt | bloczki_na_trybunie.png, uwaga użytkownika | dostawiona na wymogi licencyjne za bramką południową: rusztowanie stalowe, pomosty rzędów, czerwone krzesełka, ciemny dach na zielonych słupach; piłkochwyt z luźnej zielonej siatki na słupach | prosta, X −30…26 m (dalej na zachód), czoło 9,5 m za linią bramkową, 6 rzędów, dach 4,0–4,3 m; siatka X ±16 m, 4 m za bramką, wys. 6 m | niska (szerokość, odległość od bramki, liczba rzędów) |
| Łuk północny — sektor gości | lks16.jpg, lks18.jpg, uwaga użytkownika | goły beton, krótkie żółte barierki U w szachownicę; w zachodniej części klatka gości: wysokie czerwone ogrodzenie od czoła i przegrody w dół stopni | barierki w rzędach 3, 6, 9, 12, 15 (2,4 m co 12 m); klatka od 112° do końca łuku (145° od środka łuku, przy trybunie głównej) | niska (rozstaw barierek, granice klatki) |
| Wejścia na styku łuków z trybuną | wejscia_na_trybune/*, brama_od_luku_na_polnocy.jpg, sektor_gosci_od_bramy.jpg, il20250305_898037691/705/725/963/021/997, laczenie_trybuna_luk_poludnie.jpg, ortofotomapa, uwaga użytkownika | czop: trójkątna ściana od gruntu przy boisku wzdłuż stopni do korony i w dół skarpy, szara barierka, turkusowy cokół; schody z placu (4 stopnie, półpodest, 10 stopni) do żółtej bramy z banerem na 2,4 m, za nią krótki bieg na promenadę (3,2 m); przejazd wzdłuż czopu z bramą wjazdową (i furtką na północy); na północy otwarte bramy wjazdowe na placu, na południu ogrodzenie z siatki z żółtymi bramami i przerwą na kołowrotki (kołowrotków brak) | `tools/build_entrances.py`; łuk północny skrócony do 145,5° (149° na południu), żeby zmieściły się schody 7,2 m, przejazd 4 m i furtka; banery: północ „SEKTOR 7–12” (`34dec…`), południe „SEKTOR 1–6 / LOŻA B” (`…021`) | średnia (układ), niska (krótki bieg na promenadę, położenie bram na placu) |
| Szczyty trybuny głównej | il20250305_898037705/725 (północ), 898037963/021/039 (południe), tablica_trybuna.jpg | trójkąt przeszklenia między belką dźwigara, odciągiem i budynkiem u dołu; północ: budynek z turkusowym parterem, pasem okien, napisem RESTAURACJA i planem sektorów; południe: biała ściana, baner MOSiR na przeszkleniu, biała „budka” (koniec budynku tylnego) ze stalowymi schodami, planem sektorów i tablicą pamiątkową z czerwonym pasem | `build_grandstand.build_gables`; budynek północny 3 m głęboki (przed tunelem przęsła 0) | średnia (bryła), niska (okna, drzwi, położenie grafik) |
| Platforma kamery | grafy_na_trybunie.png, detale_trybuny_zachodniej.png | kabina z daszkiem na słupkach na koronie | 2,2 × 2,2 m, podłoga 0,5 m nad koroną, oś linii środkowej | **założenie** (położenie) |
| Bloczki z Przeplatanką | bloczki_na_trybunie.png, widok_na_trybune_z_sektora_gosci.png, uwaga użytkownika | 4–5 rzędów nad daszkiem, poniżej wyjść z tuneli, przerwy pod tunelami | 13 bloków 3,6 × 1,5 m na rzędzie 5, w osiach dźwigarów | średnia |
| Żółte barierki trybuny głównej | detale_trybuny_zachodniej.png | wzdłuż przejść, na balustradzie czołowej i na koronie | przejście w osi każdego przęsła z poręczami po obu stronach | średnia |
| Ławki rezerwowych i budka sędziego technicznego | lawka_rezerwowych.jpg, lawka_rezerwowych_closeup.jpg, il20250305_898037783/807, uwaga użytkownika | wnęka zamiast 3 pierwszych rzędów: białe otynkowane boki z szybami, tylna ściana z tablicą sponsorską ZINA / Ekstraklasa (wyprostowana ze zdjęcia), daszek z dymionej pleksi z białą krawędzią i czerwonym paskiem, słupek w osi, czerwone krzesełka przy ścianie i przedni rząd wyżej na czerwonym stelażu (na przemian czerwone i białe), sztuczna trawa przed ławką; budka sędziego technicznego: czerwony stelaż, mleczna pleksi, 3 czerwone krzesełka, kartka „SĘDZIA TECHNICZNY” | 2 × 7 m, ±12 m od linii środkowej; budka między tunelem a południową ławką (Y lokalne 62–64,2) | średnia (wymiary, położenie budki) |
| Tunel harmonijkowy | tunel_harmonijkowy.png, uwaga użytkownika | harmonijka: łuki stelaża o stałym przekroju, nożyce w ścianach bocznych, obicie w poprzeczne pasy biało-czerwone; wyciągany tylko na wyjście drużyn, w modelu złożony | na linii środkowej między ławkami, kanał 2.8 m zamiast 7 pierwszych rzędów; złożony wypełnia kanał od drzwi do wylotu (6.4 m, łuki co 0.4 m), wys. 2.4 m, szer. 2.2 m | niska (wymiary, rozstaw łuków) |
| Tunele Galery | tunel_galera.png, kolorystyka_galery_oraz_budynki_tla.png, uwaga użytkownika | dwa duże tunele przy styku z łukami, symetryczne; wcięcie o przekroju trapezu w widownię w stronę al. Unii, w głębi wylot z Przeplatanką na białym nadprożu, przed nim zwykłe ogrodzenie | Y 33–39 m i −39…−33 m, wcięcie w 10 pierwszych rzędów (u góry 6 m, dno 4,2 m), prześwit przelotu 2,6 m | średnia (wymiary) |
| Krzesełka | widok_z_galery.jpg, 516e09e1189ce, lks05, krzeselka.png (typ krzesełka) | czerwone na Galerze, czerwone/białe w sektorze dolnym | kubełki o profilu L bez nóżek, mocowane do stopnia, oparcie przy podstopniu rzędu wyżej (`build_seats.py`); instancje GPU | średnia (rozmieszczenie kolorów) |
| Ławki sektora górnego | widok_z_galery.jpg, uwaga użytkownika | jasne, kość słoniowa | malowane drewno (0,80; 0,76; 0,64) | średnia |
| Panorama bloków | lks07, lks08 (kompozycja) | kierunek: za Galerą i łukiem południowym | 12 bloków, 480–900 m (`SKYLINE` w `build_surroundings.py`) | **orientacyjna** |
| Galera | ortofotomapa | od X = 43,5 m do 69 m | od 45 do 67 m + skarpa | wysoka |
| Czoło podkowy (2010–2012) | widok_z_galery.jpg, kolorystyka_galery_oraz_budynki_tla.png, uwaga użytkownika | **bez muru i fosy**: rzędy kończą się 1–2 m przed ogrodzeniem z siatki na gruncie (lks02 z okresu żużlowego pokazuje wcześniejszy mur) | chodnik 1,5 m, pierwszy stopień 0,45 m, ogrodzenie 2,5 m (Galera), 1,2 m (łuki) | wysoka |
| Ogrodzenie z blachy (północ) | widok_na_trybune_z_sektora_gosci.png | blacha trapezowa ocynkowana ok. 2 m, słupki z zastrzałami; prosto w poprzek za bramką północną, za nim trawa przed łukiem | Y = 62 m od trybuny głównej do łuku, dalej po czole łuku do Galery; 2 m, słupki co 2,5 m | średnia (położenie z kadru) |
| Sekcje Galery | kolorystyka_galery_oraz_budynki_tla.png, uwaga użytkownika | od północy: czerwona z tunelem; 4 × biały–czerwony–biały (ostatnia z napisem ŁKS z białych krzesełek); czerwony pas u góry, niżej beton z żółtymi barierkami i tunel; siatki między sekcjami | 6 sekcji po 14 m (`GALERA_SECTIONS`), siatki na Y 28, 14, 0, −14, −28 m | średnia (granice sekcji) |
| Maszt NE / SE | cienie na ortofotomapie | (≈68, +64) / (≈68, −59) | (68, ±61,5) | średnia |
| Maszt NW / SW | brak (w cieniu trybuny) | — | (−68, ±82), bez zmian | **niezweryfikowane** |
| Konstrukcja masztów | punkt_swietlny_jupiter.png, widok_na_trybune_z_sektora_gosci.png | trzon kratownicowy, u dołu trzy rozchodzące się nogi na betonowych blokach; dodatkowe reflektory w połowie wysokości | rozejście nóg na 15 m, rozstaw stóp 8 × 7 m, pomost z 6 lampami na 25 m | średnia |
| Tablica wyników | ortofotomapa (cień), zdjęcia lks22, 19-37-09 | łuk południowy, oś boiska | (0, −110,5) | wysoka |
| Atlas Arena | ortofotomapa | środek (−174, +10), promień ok. 68 m | uproszczona bryła | średnia |
| Al. Unii Lubelskiej | ortofotomapa | pas X ≈ 78–94 m | pas asfaltu | wysoka |
| Tory (Łódź Kaliska) | ortofotomapa | pas X ≈ 115–200 m | pas tłucznia | średnia |
| Drzewa | ortofotomapa | 96 pozycji (`tools/extract_trees_from_ortho.py`) | EZ-Tree: brzoza, topola, jesion, dąb (gatunki i wysokości 14–21 m przyjęte, nie zmierzone) | średnia (pozycje), **założenie** (gatunki) |

### Przekrój trybuny głównej (do etapu tuneli)

`zdjecia/screenshot-2026-10-16_19-47-47.png`: przekrój trybuny, proj. J. Wyżnikiewicz, 1969 (autor fotografii: podpis na obrazie). Skala: 10 m = 345 px (obraz 2000 px). Odległości od balustrady czoła:

- Sektor dolny: od 0 do ok. 8,6 m, ok. 10 stopni, korona ok. 4,0 m nad terenem. Czoło na poziomie terenu przy bieżni, **bez fosy**.
- Za sektorem dolnym: komunikacja pod stropem na wysokości ok. 3,5 m (ok. 8,6–13 m).
- Sektor górny: dolna krawędź ok. 11,4 m od czoła, 5,5 m nad terenem. Górna krawędź ok. 37 m od czoła, **ok. 18,4 m nad terenem**. Nachylenie ok. 26,6°, ok. 33 rzędy po ok. 0,78 m.
- Ukośny odciąg: od spodu sektora górnego (ok. 30 m od czoła, ok. 13,7 m wysokości) do terenu ok. 38,8 m od czoła.
- Tylny budynek (podwieszony): ok. 32,5–41,5 m od czoła, od 3,5 do 7,1 m wysokości.
- Całkowita głębokość ok. 41,7 m.

Uproszczenia w modelu, żeby każdy stopień dał się przejść (podstopień poniżej 0,48 m, prześwit powyżej 2 m): sektor dolny kończy się na 3,2 m, a nie 4,0 m, a promenada leży na 3,2 m. Dachu nad sektorem górnym nie było: wizualizacja z dachem (19-46-47) to projekt, a zdjęcia (lks01, 2011…csmt8003) pokazują otwartą koronę.

## Mapa zdjęć

| Plik(i) | Co pokazuje | Do czego się przydaje |
|---|---|---|
| `ortofotomapa2013.png` | widok z góry, 2013 | kalibracja, rozmieszczenie, otoczenie |
| `56e4f97897428_o_full.jpg`, `5294b493d320e_o_medium.jpg`, `unnamed.jpg` | zdjęcia lotnicze | proporcje podkowy, maszty w narożach, sektory |
| `screenshot-…19-47-47.png` | przekrój Wyżnikiewicza (1969) | przekrój trybuny głównej |
| `screenshot-…19-46-47.png`, `…19-47-15.png` | wizualizacja projektu i zdjęcie z budowy | bryła trybuny, odciągi |
| `trybuna_od_zachodu.png`, `lks19.jpg` | tył trybuny głównej (MOSiR) | elewacja zachodnia, odciągi |
| `DSC01679.jpg` | tablica MOSiR z planem sektorów | nazwy sektorów (G, F2, F1, E2, E1, E; D goście; trybuna B; loża C; VIP boxy) |
| `widok_z_galery.jpg` | widok z sektora E (Galera) na trybunę główną, ok. 2010–2012 | brak fosy; ogrodzenie (pełne brązowe panele u dołu, siatka wyżej); trawa zamiast bieżni; podział daszku sektora dolnego (biały–czerwony–biały, długi biały na N); maszt SW tuż za południowym końcem trybuny głównej; tablica na łuku południowym |
| `widok_na_zegar_u2.png` | łuk południowy nocą, ok. 2010–2012 (fotopolska), z trybuny głównej — lewo to wschód | czerwone krzesełka we wschodniej połowie łuku (4 bloki, betonowe zejścia, krótkie żółte barierki), zachodnia połowa to goły beton z żółtymi barierkami; **niskie** ogrodzenie (~1,2 m, biało-czerwone słupki) na łuku; ciemny ślad bieżni w trawie; bandy reklamowe na słupach na koronie; maszt SE za łukiem |
| `bloczki_na_trybunie.png` | z trybuny głównej na łuk południowy i Galerę | balustrada czołowa sektora górnego: betonowe bloki z graffiti i żółtą poręczą nad daszkiem; **tymczasowa trybuna za bramką południową** pod tablicą wyników (stalowe rusztowanie, czerwone krzesełka, ciemny dach na zielonych słupach) z piłkochwytem z zielonej siatki; bandy na koronie łuku i Galery |
| `detale_trybuny_zachodniej.png` | sektor górny trybuny głównej z bliska | żółte poręcze wzdłuż przejść i rzędów, graffiti na murkach, **reflektory na słupach na koronie**, platforma kamery, anteny GSM |
| `widok_na_trybune_z_sektora_gosci.png` | z sektora gości (NE) na trybunę główną | tunel w każdym przęśle (żółte obrzeża), bloczki z Przeplatanką poniżej wyjść z tuneli, przejścia z żółtymi poręczami; Atlas Arena tuż za trybuną; w północnej części długi biały pawilon (loże/VIP) przed sektorem dolnym; **pełne ogrodzenie z blachy** przy łuku północnym |
| `516e09e41f411…`, `516e09e800a6f…`, `516e09e9f3933…`, `516e09e31b4d3…` | łuki i Galera z ogrodzeniem | mur czołowy, ogrodzenie, wyjścia ewakuacyjne |
| `516e09e1189ce…`, `516e09e210a69…`, `lks05.jpg`, `lks04.jpg` | sektor dolny pod daszkiem | krzesełka, konstrukcja daszku, fasada lóż |
| `4ff5cb…` (3 pliki, cz-b) | trybuna główna i bieżnia z torami | bieżnia lekkoatletyczna z liniami torów (okres wcześniejszy) |
| `lks02.jpg` | łuk z bieżnią żużlową (okres wcześniejszy) | mur czołowy łuku — w latach 2010–2012 już go nie było |
| `kolorystyka_galery_oraz_budynki_tla.png` | kadr z transmisji, z trybuny głównej na Galerę | sekcje kolorystyczne krzesełek Galery, tunele z Przeplatanką, siatki między sekcjami, zabudowa za torami |
| `jupitery_dajace_plamy_swietlne.png` | kadr z transmisji o zmierzchu (ŁKS – Pogoń) | jupitery dają wyraźne, jasne plamy światła na murawie z ciemniejszymi strefami między nimi — wzorzec do oświetlenia nocnego (Faza 4) |
| `lks22.jpg`, `screenshot-…19-37-09.png` | tablica wyników z zegarem | tekstura i proporcje tablicy |
| `jupiter.png` | głowica masztu | głowica (odwrócony trapez) |
| `34dec5jwrh…jpeg` | schody wejściowe z bramą „ŁKS WITA” | wejścia (tunele) |
| `DSC01675.jpg`, `DSC01677.jpg` | brama z herbem, mur oporowy od zewnątrz | ogrodzenie zewnętrzne, bramy |
| `lks07`–`lks18`, `07lks3_*`, `20100421csmt8013.jpg` | mecze, kibice, noc | oprawy, banery, oświetlenie nocne (Faza 4) |
| `punkt_swietlny_jupiter.png` | maszt od strony trybuny, kadr z transmisji | nogi rozchodzące się u dołu, reflektory w połowie wysokości |
| `lawka_rezerwowych.png` | kadr z transmisji (ŁKS – Pogoń) | ławka rezerwowych: pleksi na biało-czerwonym stelażu |
| `tunel_harmonijkowy.png` | kadr z transmisji (ŁKS – Cracovia) | wnętrze tunelu wyjścia piłkarzy: nożycowy stelaż ścian, pasy biało-czerwone |
| `wejscia_na_trybune/*`, `trapez-murpng.png`, `laczenie_trybuna_luk_poludnie.jpg` | wejścia z placu na styku łuków z trybuną główną, czop łuku, plan sektorów MOSiR | schody, bramy, banery; grafiki wyprostowane w `generate_entrance_textures` |
| `tunel_galera.png` | kadr z transmisji, Galera przy łuku północnym | duży tunel wejściowy z podestem i żółtymi poręczami |
| `pod_zegarem.png` | kadr z transmisji, łuk południowy | sektory krzesełek i ławek łuku, bandy na koronie, tablica wyników |
| `krzeselka.png` | stadion Zbrojovki Brno (nie ŁKS) — ten sam typ krzesełek | kształt: zaokrąglony profil L, bez nóżek, przykręcone do stopnia, lśniący plastik |
| `grafy_na_trybunie.png`, `screenshot-…19-36-47.png` | północna część trybuny głównej od boiska | mural „Tutaj wychowani … wierni i oddani” na balustradzie czołowej, graffiti dzielnic na bloczkach (…DZIANE, STARE, POLESIE, TOLECHÓW — w modelu pominięte), platforma kamery na koronie, pawilon VIP z białym daszkiem — mural wyprostowany z tego zdjęcia (`generate_mural_texture`) |

## Zasoby zewnętrzne w modelu

| Zasób | Autor / źródło | Licencja | Gdzie |
|---|---|---|---|
| EZ-Tree (generator drzew, tekstury liści) | Daniel Greenheck, [github.com/dgreenheck/ez-tree](https://github.com/dgreenheck/ez-tree) | MIT (zachować notkę o prawach autorskich: `node_modules/@dgreenheck/ez-tree/LICENSE`) | `public/assets/drzewa.glb` (`npm run trees:build`) |
| Kora dębu i wierzby | [Poly Haven](https://polyhaven.com/a/bark_brown_02) (bark_brown_02, bark_willow_02) | CC0 | j.w., przez EZ-Tree |
| Kora brzozy i sosny | [TextureCan](https://www.texturecan.com/terms/) | CC0 | j.w., przez EZ-Tree |
| HDRI Overcast Soil (Pure Sky) | [Poly Haven](https://polyhaven.com/a/overcast_soil_puresky) | CC0 | `public/assets/env/` |
| Trawa (murawa, teren) | ambientCG | CC0 | `assets/textures/grass/` |
| Blacha trapezowa (CorrugatedSteel005) | [ambientCG](https://ambientcg.com/a/CorrugatedSteel005) | CC0 | `assets/textures/corrugated_steel/` |

Autorstwo większości zdjęć jest nieznane. Przed publikacją projektu trzeba ustalić licencje albo usunąć zdjęcia z repozytorium.

## Otwarte pytania

1. **Tunele**: liczba (w każdym przęśle) i wyjścia na widownię są ze zdjęć; przebieg schodów w hali pod trybuną to założenie. Jeśli znajdzie się zdjęcie wejść od strony hali, warto je zweryfikować.
2. **Maszty zachodnie**: `widok_z_galery.jpg` pokazuje maszt SW tuż za południowym końcem trybuny głównej. Model ma (−68, −82), czyli ok. 10–15 m dalej na południe. Potrzebny drugi kąt, żeby to ustalić.
3. **Łuk północny**: na ortofotomapie zewnętrzną część zasłaniają drzewa; model zakłada tę samą głębokość co Galera.
4. **Okres**: model pokazuje stan z lat 2010–2012 (decyzja z 17.10.2026), stąd trawa zamiast bieżni i plastikowe krzesełka.
6. **Panorama bloków**: pozycje i wysokości to kompozycja ze zdjęć lks07/lks08, bez pomiaru. Do zweryfikowania na mapie (rejon Karolewa / za stacją Łódź Kaliska).
13. **Sektor gości na planie MOSiR** (`DSC01679.jpg`): sektor D leży w środku łuku północnego, ze strefami buforowymi po obu stronach; model (wg `lks16.jpg`) ma klatkę przy trybunie głównej. Plan może pochodzić z innego okresu. Na planie „Trybuna B” to prosta trybuna za bramką południową (tymczasowa).
7. **Łuk północny (sektor gości)**: goły beton z żółtymi barierkami U i klatka gości z wysokiego czerwonego ogrodzenia (`lks16.jpg`, `lks18.jpg`, uwaga użytkownika). Rozstaw barierek i zasięg klatki (od 112° do końca łuku) to przybliżenie ze zdjęć; band na koronie brak.
9. **Granica ogrodzeń**: wysokie ogrodzenie stoi tylko na prostej Galery, niskie na łuku południowym i na łuku północnym za blachą. Dokładnego miejsca przejścia nie ma na zdjęciach.
11. **Do dodania ze zdjęć z 2012 r.**: biały daszek nad pawilonem VIP (na `grafy_na_trybunie.png`; model w przęsłach 0–3 go nie ma).
12. **Mural i platforma kamery**: długość muralu (ok. 35 m, przęsła 0,5–4,3) oszacowana z podziału na przęsła na zdjęciu; platforma kamery postawiona w osi linii środkowej (typowe miejsce), na zdjęciu jej położenie wzdłuż trybuny jest niepewne.
10. **Bandy na koronie**: 4 tablice z napisami odczytanymi z `widok_na_zegar_u2.png`; pozycje orientacyjne, łuk północny bez band.
8. **Barierki**: żółte poręcze przy przejściach Galery, krótkie barierki w blokach krzesełek łuku południowego i poprzeczne na jego betonowej połowie są w modelu; ich dokładny przebieg to przybliżenie ze zdjęć.
5. **Chodnik przed pierwszym rzędem**: 1,5 m i pierwszy stopień 0,45 m oszacowane ze zdjęć. Brak wymiaru.
