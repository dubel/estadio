"""
Generowanie podkowy trybun na wałach ziemnych (łuki i Galera z sekcjami krzesełek i tunelami),
murawy z zarośniętą bieżnią, ogrodzeń oraz historycznej tablicy świetlnej z zegarem.
"""

import bpy
import bmesh
import mathutils
import math

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_seats import place_seats, seat_material, seats_in_row, SEAT_PITCH, SEAT_BACK_GAP  # noqa: E402
from build_grandstand import _beam, _extrude_profile, _rail, PRZEPLATANKA_ASPECT  # noqa: E402
import mathutils  # noqa: E402

STRAIGHT_L = 84.0  # długość prostych bieżni 400 m (środki łuków w Y = ±42 m)


def stadium_path(r, ang_start, ang_end, arc_step_deg=4.0, straight_step=3.0, close_west=False):
    """
    Punkty (x, y, nx, ny) na obrysie „stadionowym” (2 łuki + proste) w odległości r od osi bieżni,
    od kąta ang_start (0..180°, łuk północny) zgodnie z ruchem wskazówek zegara przez prostą
    wschodnią do ang_end (-180..0°, łuk południowy). Proste są dzielone co straight_step metrów —
    jeden quad na całą prostą dawał 89-metrowe trójkąty, na których kapsuła gracza się zacinała.
    close_west dokłada punkty prostej zachodniej (pełna pętla).
    """
    cy = STRAIGHT_L / 2.0
    pts = []

    def arc(a0, a1, c):
        n = max(1, math.ceil(abs(a1 - a0) / arc_step_deg))
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((r * math.cos(a), c + r * math.sin(a), math.cos(a), math.sin(a)))

    def straight(x, y0, y1, nx):
        n = max(1, math.ceil(abs(y1 - y0) / straight_step))
        for i in range(1, n):
            pts.append((x, y0 + (y1 - y0) * i / n, nx, 0.0))

    arc(ang_start, 0.0, cy)
    straight(r, cy, -cy, 1.0)
    arc(0.0, ang_end, -cy)
    if close_west:
        straight(-r, -cy, cy, -1.0)
    return pts

def build_pitch_and_track(col, mats):
    """Tworzy murawę oraz pas dawnej bieżni 400 m (w latach 2010–2012 porośnięty trawą)."""
    PITCH_L = 105.0
    PITCH_W = 68.0
    
    # 1. Płyta murawy z pasami bocznymi (112m x 74m)
    bm_pitch = bmesh.new()
    bmesh.ops.create_grid(bm_pitch, x_segments=1, y_segments=1, size=1.0)
    # create_grid(size=1) daje wierzchołki ±1, więc skala to POŁOWA wymiaru (wcześniej płyta miała 148 x 224 m
    # i przykrywała plac pod trybunami)
    bmesh.ops.scale(bm_pitch, vec=(37.0, 56.0, 1.0), verts=bm_pitch.verts)
    
    # Warstwa współrzędnych UV dla murawy
    uv_layer = bm_pitch.loops.layers.uv.verify()
    for face in bm_pitch.faces:
        for loop in face.loops:
            u = (loop.vert.co.x + 37.0) / 74.0
            v = (loop.vert.co.y + 56.0) / 112.0
            loop[uv_layer].uv = (u, v)

    mesh_pitch = bpy.data.meshes.new("Murawa_Boisko_Mesh")
    bm_pitch.normal_update()
    bm_pitch.to_mesh(mesh_pitch)
    bm_pitch.free()
    
    obj_pitch = bpy.data.objects.new("Murawa_Boisko", mesh_pitch)
    if mats and 'grass' in mats:
        obj_pitch.data.materials.append(mats['grass'])
    col.objects.link(obj_pitch)

    # Trawiaste wnętrze bieżni (łuki za bramkami), 2 cm pod płytą boiska
    bm_in = bmesh.new()
    bm_in.faces.new([bm_in.verts.new((x, y, -0.02)) for x, y, _, _ in stadium_path(37.0, 180.0, -180.0, close_west=True)])
    mesh_in = bpy.data.meshes.new("Murawa_Wnetrze_Biezni_Mesh")
    bm_in.normal_update()
    bm_in.to_mesh(mesh_in)
    bm_in.free()
    obj_in = bpy.data.objects.new("Murawa_Wnetrze_Biezni", mesh_in)
    obj_in.data.materials.append(mats['ground_grass'])
    col.objects.link(obj_in)

    # 2. Bieżnia lekkoatletyczna (czerwono-grafitowy żużel)
    # Mieści się POMIĘDZY boiskiem a trybunami (zarówno podkową, jak i Trybuną Główną)
    R_IN = 37.0
    R_OUT = 45.0  # szerokość bieżni 8.0 m
    NUM_ARC_SEGS = 32
    
    bm_track = bmesh.new()
    pts_in = []
    pts_out = []
    
    # Łuk północny (+Y)
    for i in range(NUM_ARC_SEGS + 1):
        ang = math.pi * (i / NUM_ARC_SEGS)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cy = STRAIGHT_L / 2.0
        pts_in.append((R_IN * cos_a, cy + R_IN * sin_a, 0.02))
        pts_out.append((R_OUT * cos_a, cy + R_OUT * sin_a, 0.02))
        
    # Łuk południowy (-Y)
    for i in range(NUM_ARC_SEGS + 1):
        ang = math.pi + math.pi * (i / NUM_ARC_SEGS)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cy = -STRAIGHT_L / 2.0
        pts_in.append((R_IN * cos_a, cy + R_IN * sin_a, 0.02))
        pts_out.append((R_OUT * cos_a, cy + R_OUT * sin_a, 0.02))
        
    v_in = [bm_track.verts.new(p) for p in pts_in]
    v_out = [bm_track.verts.new(p) for p in pts_out]
    n_pts = len(v_in)
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        bm_track.faces.new([v_in[i], v_out[i], v_out[next_i], v_in[next_i]])
        
    mesh_track = bpy.data.meshes.new("Bieznia_Zarosnieta_Mesh")
    bm_track.normal_update()
    bm_track.to_mesh(mesh_track)
    bm_track.free()
    
    # Stan 2010–2012: bieżnia zarośnięta trawą aż do ogrodzenia (widok_z_galery.jpg, ortofotomapa 2013)
    obj_track = bpy.data.objects.new("Bieznia_Zarosnieta", mesh_track)
    obj_track.data.materials.append(mats['ground_grass'])
    col.objects.link(obj_track)

    return obj_pitch, obj_track


def build_pitch_lines(col, mats):
    """Tworzy kredowe linie boiska piłkarskiego 105 x 68 m (zgodne z przepisami FIFA/PZPN)."""
    bm = bmesh.new()
    LW = 0.12 # szerokość linii 12 cm
    Z_LINE = 0.025 # 2.5 cm nad murawą
    
    def add_line_segment(p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length < 1e-4:
            return
        nx = -dy / length * (LW / 2.0)
        ny =  dx / length * (LW / 2.0)
        v0 = bm.verts.new((p1[0] - nx, p1[1] - ny, Z_LINE))
        v1 = bm.verts.new((p1[0] + nx, p1[1] + ny, Z_LINE))
        v2 = bm.verts.new((p2[0] + nx, p2[1] + ny, Z_LINE))
        v3 = bm.verts.new((p2[0] - nx, p2[1] - ny, Z_LINE))
        bm.faces.new([v0, v1, v2, v3])
        
    def add_circle_ring(cx, cy, radius, num_segs=48, start_ang=0.0, end_ang=2.0*math.pi):
        d_ang = (end_ang - start_ang) / num_segs
        pts_in = []
        pts_out = []
        for i in range(num_segs + 1):
            ang = start_ang + i * d_ang
            ca = math.cos(ang)
            sa = math.sin(ang)
            pts_in.append(bm.verts.new((cx + (radius - LW/2.0) * ca, cy + (radius - LW/2.0) * sa, Z_LINE)))
            pts_out.append(bm.verts.new((cx + (radius + LW/2.0) * ca, cy + (radius + LW/2.0) * sa, Z_LINE)))
        for i in range(num_segs):
            bm.faces.new([pts_in[i], pts_out[i], pts_out[i+1], pts_in[i+1]])

    def add_spot(cx, cy, r=0.18, num_segs=16):
        v_center = bm.verts.new((cx, cy, Z_LINE))
        rim = []
        for i in range(num_segs):
            ang = 2.0 * math.pi * (i / num_segs)
            rim.append(bm.verts.new((cx + r * math.cos(ang), cy + r * math.sin(ang), Z_LINE)))
        for i in range(num_segs):
            bm.faces.new([v_center, rim[i], rim[(i+1)%num_segs]])

    # 1. Linie obwodowe (105 x 68 m)
    add_line_segment((-34.0, -52.5), ( 34.0, -52.5)) # południowa linia bramkowa
    add_line_segment((-34.0,  52.5), ( 34.0,  52.5)) # północna linia bramkowa
    add_line_segment((-34.0, -52.5), (-34.0,  52.5)) # zachodnia linia boczna
    add_line_segment(( 34.0, -52.5), ( 34.0,  52.5)) # wschodnia linia boczna

    # 2. Linia środkowa i koło środkowe (R = 9.15 m)
    add_line_segment((-34.0, 0.0), (34.0, 0.0))
    add_circle_ring(0.0, 0.0, 9.15, num_segs=64)
    add_spot(0.0, 0.0)

    # 3. Pola karne (16.5 m od linii i 16.5 m od słupków: X od -20.16 do +20.16)
    for sign_y in [-1, 1]:
        gy = sign_y * 52.5
        fy = sign_y * 36.0 # 52.5 - 16.5 = 36.0
        add_line_segment((-20.16, gy), (-20.16, fy))
        add_line_segment(( 20.16, gy), ( 20.16, fy))
        add_line_segment((-20.16, fy), ( 20.16, fy))
        
        # Pole bramkowe (5.5 m od linii i 5.5 m od słupków: X od -9.16 do +9.16)
        by = sign_y * 47.0 # 52.5 - 5.5 = 47.0
        add_line_segment((-9.16, gy), (-9.16, by))
        add_line_segment(( 9.16, gy), ( 9.16, by))
        add_line_segment((-9.16, by), ( 9.16, by))

        # Punkt karny (11.0 m od linii bramkowej)
        py = sign_y * 41.5
        add_spot(0.0, py)

        # Łuk pola karnego (R = 9.15 m wokół punktu karnego na zewnątrz pola)
        alpha = math.acos(5.5 / 9.15)
        if sign_y < 0:
            add_circle_ring(0.0, py, 9.15, num_segs=24, start_ang=math.pi/2.0 - alpha, end_ang=math.pi/2.0 + alpha)
        else:
            add_circle_ring(0.0, py, 9.15, num_segs=24, start_ang=-math.pi/2.0 - alpha, end_ang=-math.pi/2.0 + alpha)

    # 4. Łuki narożne (R = 1.0 m w 4 narożnikach)
    add_circle_ring(-34.0, -52.5, 1.0, num_segs=12, start_ang=0.0, end_ang=math.pi/2.0)
    add_circle_ring( 34.0, -52.5, 1.0, num_segs=12, start_ang=math.pi/2.0, end_ang=math.pi)
    add_circle_ring( 34.0,  52.5, 1.0, num_segs=12, start_ang=math.pi, end_ang=1.5*math.pi)
    add_circle_ring(-34.0,  52.5, 1.0, num_segs=12, start_ang=1.5*math.pi, end_ang=2.0*math.pi)

    mesh_lines = bpy.data.meshes.new("Linie_Boiska_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh_lines)
    bm.free()

    obj_lines = bpy.data.objects.new("Linie_Boiska", mesh_lines)
    if mats and 'pitch_lines' in mats:
        obj_lines.data.materials.append(mats['pitch_lines'])
    col.objects.link(obj_lines)
    return obj_lines


R_TRACK_OUT = 45.0     # ogrodzenie z siatki na gruncie przy zewnętrznej krawędzi dawnej bieżni
FRONT_WALK = 1.5       # chodnik między ogrodzeniem a pierwszym rzędem — muru oporowego nie było
                       # (widok_z_galery.jpg, kolorystyka_galery_oraz_budynki_tla.png)
ROW0_H = 0.45          # wysokość pierwszego stopnia nad chodnikiem
FENCE_H = 2.5          # stalowe ogrodzenie na gruncie: pełne panele u dołu, siatka wyżej (widok_z_galery.jpg)
# Końce podkowy przy trybunie głównej (kąt od środka łuku, 0° = wschód). Na południu czop leży na cieniu
# z ortofotomapy; na północy łuk jest krótszy: między końcem trybuny a czopem mieszczą się schody, przejazd
# z bramą wjazdową i furtka (brama_od_luku_na_polnocy.jpg, il20250305_898037691), jasny pas na ortofotomapie.
BOWL_ANGLE_N = 145.5
BOWL_ANGLE_S = 149.0
STAND_DEPTH = 22.0     # głębokość widowni na wale ziemnym
STAND_H = 6.8          # wysokość korony wału (na niej stoi tablica wyników, build_scoreboard)
NUM_STEPS = 20         # 20 betonowych stopni
STEP_D = STAND_DEPTH / NUM_STEPS
STEP_H = (STAND_H - ROW0_H) / (NUM_STEPS - 1)  # ~0.33 m
STAND_BACK = R_TRACK_OUT + FRONT_WALK + STAND_DEPTH   # tylna krawędź korony
LOW_FENCE_H = 1.2      # niskie ogrodzenie łuków z biało-czerwonymi słupkami (widok_na_zegar_u2.png)

# Łuk południowy (kąty jak w stadium_path, środek łuku w Y = -42 m; -90° to oś pod zegarem), widok_na_zegar_u2.png:
# wschodnia połowa (od Galery do osi) czerwone krzesełka w 4 blokach rozdzielonych betonowymi zejściami,
# w blokach krótkie żółte barierki; zachodnia połowa (ku trybunie głównej) goły beton z żółtymi barierkami
SOUTH_SEAT_ARC = (-88.0, -4.0)
SOUTH_AISLES = (-67.0, -46.0, -25.0)       # osie zejść między blokami
SOUTH_AISLE_W = 1.4
SOUTH_BLOCK_RAIL_ROWS = (6, 13)
SOUTH_BLOCK_RAIL_LEN = 3.0
SOUTH_CONCRETE_ARC = (-149.0, -92.0)
SOUTH_CONCRETE_RAIL_ROWS = (6, 12)
# Łuk północny (sektor gości, lks16.jpg, lks18.jpg): goły beton, krótkie żółte barierki w kształcie U rozstawione
# w szachownicę co 3 rzędy; w zachodniej części, przy trybunie głównej, klatka gości z wysokiego czerwonego
# ogrodzenia: przegroda w dół stopni na GUEST_ARC[0] i przy trybunie głównej, wysokie ogrodzenie od czoła.
# Kąty od środka łuku (0, STRAIGHT_L / 2): 0° to wschód (Galera), 90° oś boiska, BOWL_ANGLE_N trybuna główna.
NORTH_ARC = (6.0, BOWL_ANGLE_N - 2.0)
NORTH_RAIL_ROWS = (3, 6, 9, 12, 15)
NORTH_RAIL_LEN, NORTH_RAIL_PERIOD = 2.4, 12.0  # długość barierki i rozstaw wzdłuż rzędu (metry)
GUEST_ARC = (112.0, BOWL_ANGLE_N - 0.5)

# Galera od północy (kolorystyka_galery_oraz_budynki_tla.png): 6 sekcji rozdzielonych siatką od chodnika
# po koronę. (y_od, y_do, kolorystyka, oś przejścia):
# red — same czerwone krzesełka (z tunelem); bcb — od góry cienki pas biały, gruby czerwony, cienki biały;
# lks — jak bcb, na czerwonym pasie pikselowy napis ŁKS z białych krzesełek;
# top_red — czerwony pas w górnych rzędach, niżej goły beton z żółtymi barierkami (z tunelem).
GALERA_SECTIONS = [(28.0, 42.0, 'red', 30.5), (14.0, 28.0, 'bcb', 21.0), (0.0, 14.0, 'bcb', 7.0),
                   (-14.0, 0.0, 'bcb', -7.0), (-28.0, -14.0, 'lks', -26.5), (-42.0, -28.0, 'top_red', -30.5)]
GALERA_PARTITIONS = (28.0, 14.0, 0.0, -14.0, -28.0)
BCB_WHITE_LOW, BCB_WHITE_HIGH = 4, 17      # rzędy < 4 i >= 17 białe
TOP_RED_FROM = 15                          # sekcja top_red: czerwone od rzędu 15
LKS_ROWS = (6, 12)                         # napis: rzędy 6–12 (7 pikseli wysokości)
LKS_FONT = [                               # 5 × 7, od góry; Ł, K, S rozdzielone pustą kolumną
    ".#....#...#..###.",
    ".#....#..#..#...#",
    ".##...#.#...#....",
    "##....##.....###.",
    ".#....#.#.......#",
    ".#....#..#..#...#",
    ".####.#...#..###.",
]

# Dwa tunele wejściowe Galery w sekcjach skrajnych (tunel_galera.png — północny, południowy symetrycznie):
# wcięcie o przekroju trapezu w widownię od chodnika w stronę al. Unii, w jego głębi wylot przelotu pod
# wałem z Przeplatanką na białym nadprożu. Przed wcięciem zwykłe ogrodzenie. Zakresy Y leżą na
# wierzchołkach podziału prostej (co 3 m, stadium_path).
GALERA_TUNNELS = ((-39.0, -33.0), (33.0, 39.0))
TUNNEL_OPEN_H = 2.6     # prześwit przelotu
TUNNEL_SLOPE = 0.9      # pochylenie ścian wcięcia: dno i wylot 4.2 m, u góry pełne 6 m
TUNNEL_ROWS = 10        # głębokość wcięcia w rzędach; wylot pod rzędem 10 (nadproże 2.6–3.8 m)
# Ogrodzenie z blachy trapezowej na północnym krańcu (widok_na_trybune_z_sektora_gosci.png): prosto w poprzek
# ok. 9.5 m za linią bramkową od trybuny głównej do łuku, dalej po czole łuku do Galery. Położenie z kadru,
# bez pomiaru. Na odcinku łuku zastępuje niskie ogrodzenie.
SHEET_FENCE_Y = 62.0
SHEET_FENCE_H = 2.0
SHEET_TILE_M = 1.4      # 8 przetłoczeń na kafel: rozstaw ok. 17 cm
# Trybuna tymczasowa za bramką południową, pod tablicą wyników (bloczki_na_trybunie.png): dostawiona
# na wymogi licencyjne, rusztowanie ze stalowych rur, pomosty rzędów z blachy, czerwone krzesełka, ciemny dach
# na zielonych słupach. Prosta, równoległa do linii bramkowej, na płaskim terenie przed łukiem. Na zdjęciu
# sięga dalej na zachód niż na wschód od bramki. Przed nią piłkochwyt: zielona siatka na słupach.
TEMP_STAND_X = (-30.0, 26.0)
TEMP_STAND_FRONT_Y = -62.0                 # 9.5 m za linią bramkową, jak blacha na północy
TEMP_ROWS, TEMP_ROW_D, TEMP_ROW_H, TEMP_DECK0 = 6, 0.8, 0.35, 0.5
TEMP_AISLES = (-16.0, -2.0, 12.0)          # osie przejść między sektorami
TEMP_AISLE_W = 1.2
TEMP_BAY = 2.5                             # rozstaw stojaków rusztowania
TEMP_ROOF_Z = (4.3, 4.0)                   # spód dachu: przód, tył (spadek do tyłu)
TEMP_ROOF_POST_EVERY = 5.0
BALL_NET_X, BALL_NET_Y, BALL_NET_H = (-16.0, 16.0), -58.5, 6.0
BALL_NET_POST_EVERY, BALL_NET_SAG = 4.0, 0.3   # luźna siatka: lina między słupami ugina się o BALL_NET_SAG
SOUTH_ADS = [(-38.0, 0), (-51.0, 1), (-64.0, 2), (-77.0, 3)]   # bandy na koronie nad krzesełkami: (kąt, wiersz atlasu), od wschodu


def _obox(bm, center, size, yaw=0.0, pitch=0.0):
    """Prostopadłościan o wymiarach size=(dx, dy, dz), obrócony o yaw (wokół Z) i pitch (wokół lokalnego Y)."""
    m = (mathutils.Matrix.Translation(center) @ mathutils.Matrix.Rotation(yaw, 4, 'Z')
         @ mathutils.Matrix.Rotation(pitch, 4, 'Y') @ mathutils.Matrix.Diagonal((*size, 1.0)))
    return bmesh.ops.create_cube(bm, size=1.0, matrix=m)


def _row(i):
    """(odległość przodu stopnia od czoła, wysokość stopnia) rzędu i podkowy."""
    return FRONT_WALK + i * STEP_D, ROW0_H + i * STEP_H


def _arc_point(r, ang_deg, cy=-42.0):
    a = math.radians(ang_deg)
    return (r * math.cos(a), cy + r * math.sin(a)), a


def _in_galera_tunnel(y, margin=0.0):
    return any(a - margin <= y <= b + margin for a, b in GALERA_TUNNELS)


def _finish_mesh(col, bm, name, mats_list):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    for m in mats_list:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def build_bowl(col, mats):
    """
    Podkowa trybun na wałach ziemnych: od łuku północnego przez prostą wschodnią (Galera) do łuku
    południowego. Przy zewnętrznej krawędzi dawnej bieżni ogrodzenie na gruncie, za nim chodnik
    FRONT_WALK, dalej 20 betonowych stopni i tylna skarpa. Muru oporowego ani fosy nie było
    (widok_z_galery.jpg, kolorystyka_galery_oraz_budynki_tla.png). Strona zachodnia pozostaje wolna
    na Trybunę Główną.
    """
    bm_bowl = bmesh.new()
    bowl_rings = []
    bowl_path = stadium_path(R_TRACK_OUT, BOWL_ANGLE_N, -BOWL_ANGLE_S)
    for px, py, nx, ny in bowl_path:
        b_pts = [(px + nx * FRONT_WALK, py + ny * FRONT_WALK, -0.05)]
        for s in range(NUM_STEPS):
            d, z = _row(s)
            b_pts += [(px + nx * d, py + ny * d, z), (px + nx * (d + STEP_D), py + ny * (d + STEP_D), z)]
        d_back = FRONT_WALK + STAND_DEPTH + 5.0                  # stopa tylnej skarpy
        b_pts.append((px + nx * d_back, py + ny * d_back, 0.0))
        bowl_rings.append([bm_bowl.verts.new(p) for p in b_pts])

    for i in range(len(bowl_rings) - 1):
        (_, ya, nxa, _), (_, yb, nxb, _) = bowl_path[i], bowl_path[i + 1]
        if nxa == 1.0 and nxb == 1.0 and _in_galera_tunnel(ya, 1e-6) and _in_galera_tunnel(yb, 1e-6):
            continue                                   # przęsło tunelu Galery (build_galera_tunnels)
        bA = bowl_rings[i]
        bB = bowl_rings[i + 1]
        for j in range(len(bA) - 1):
            bm_bowl.faces.new([bA[j], bB[j], bB[j+1], bA[j+1]])

    mesh_bowl = bpy.data.meshes.new("Trybuna_Podkowa_Mesh")
    bm_bowl.normal_update()
    bm_bowl.to_mesh(mesh_bowl)
    bm_bowl.free()
    obj_bowl = bpy.data.objects.new("Trybuna_Podkowa", mesh_bowl)
    obj_bowl.data.materials.append(mats['concrete'])
    col.objects.link(obj_bowl)

    # Wysokie ogrodzenie na gruncie przed Galerą (prosta) i siatki między jej sekcjami: panele z teksturą
    # alfa (u w metrach / 2.5 m przęsła). Dwie ściany 4 cm od siebie: kolizje Octree w Three.js są
    # jednostronne, pojedyncza płaszczyzna przepuszczała gracza. Na łukach niskie ogrodzenie (build_bowl_details).
    bm_f = bmesh.new()
    uv = bm_f.loops.layers.uv.verify()

    def panel(corners, flip):
        """corners: (x, y, z, u, v) w kolejności obiegu; flip odwraca lico."""
        if flip:
            corners = corners[::-1]
        face = bm_f.faces.new([bm_f.verts.new(c[:3]) for c in corners])
        for loop, c in zip(face.loops, corners):
            loop[uv].uv = (c[3] / 2.5, c[4])

    path = stadium_path(R_TRACK_OUT, BOWL_ANGLE_N, -BOWL_ANGLE_S)
    for off, flip in [(0.02, False), (0.06, True)]:
        dist = 0.0
        for (x0, y0, nx0, ny0), (x1, y1, nx1, ny1) in zip(path, path[1:]):
            seg = math.hypot(x1 - x0, y1 - y0)
            if abs(ny0) > 1e-6 or abs(ny1) > 1e-6:   # odcinek łuku
                continue
            a0 = (x0 + nx0 * off, y0 + ny0 * off)
            a1 = (x1 + nx1 * off, y1 + ny1 * off)
            panel([(*a0, 0.0, dist, 0.0), (*a1, 0.0, dist + seg, 0.0),
                   (*a1, FENCE_H, dist + seg, 1.0), (*a0, FENCE_H, dist, 1.0)], flip)
            dist += seg
    for yp in GALERA_PARTITIONS:
        for off, flip in [(-0.02, False), (0.02, True)]:
            for i in range(NUM_STEPS):
                d, z = _row(i)
                xa, xe = R_TRACK_OUT + d, R_TRACK_OUT + d + STEP_D
                panel([(xa, yp + off, z, xa, 0.0), (xe, yp + off, z, xe, 0.0),
                       (xe, yp + off, z + FENCE_H, xe, 1.0), (xa, yp + off, z + FENCE_H, xa, 1.0)], flip)
    # Klatka sektora gości na łuku północnym: przegrody w dół stopni i wysokie ogrodzenie od czoła
    cy = STRAIGHT_L / 2
    for ang in GUEST_ARC:
        (tx, ty), a = _arc_point(1.0, ang, cy)
        t = (-math.sin(a), math.cos(a))                      # styczna do łuku
        for off, flip in [(-0.02, False), (0.02, True)]:
            for i in range(NUM_STEPS):
                d, z = _row(i)
                ra, re = R_TRACK_OUT + d, R_TRACK_OUT + d + STEP_D
                pa, _ = _arc_point(ra, ang, cy)
                pe, _ = _arc_point(re, ang, cy)
                pa, pe = (pa[0] + t[0] * off, pa[1] + t[1] * off), (pe[0] + t[0] * off, pe[1] + t[1] * off)
                panel([(*pa, z, ra, 0.0), (*pe, z, re, 0.0), (*pe, z + FENCE_H, re, 1.0), (*pa, z + FENCE_H, ra, 1.0)], flip)
    n = round((GUEST_ARC[1] - GUEST_ARC[0]) / 3.0)
    for off, flip in [(0.02, True), (0.06, False)]:
        r = R_TRACK_OUT + off
        for k in range(n):
            a0 = GUEST_ARC[0] + k * (GUEST_ARC[1] - GUEST_ARC[0]) / n
            a1 = GUEST_ARC[0] + (k + 1) * (GUEST_ARC[1] - GUEST_ARC[0]) / n
            (p0, _), (p1, _) = _arc_point(r, a0, cy), _arc_point(r, a1, cy)
            u0, u1 = r * math.radians(a0), r * math.radians(a1)
            panel([(*p0, 0.0, u0, 0.0), (*p1, 0.0, u1, 0.0), (*p1, FENCE_H, u1, 1.0), (*p0, FENCE_H, u0, 1.0)], flip)
    mesh_f = bpy.data.meshes.new("Ogrodzenie_Trybun_Mesh")
    bm_f.normal_update()
    bm_f.to_mesh(mesh_f)
    bm_f.free()
    obj_f = bpy.data.objects.new("Ogrodzenie_Trybun", mesh_f)
    obj_f.data.materials.append(mats['fence'])
    col.objects.link(obj_f)

    # Krzesełka Galery według sekcji; w sekcji top_red pod czerwonym pasem żółte barierki na gołym betonie
    red, white = [], []
    bm_y = bmesh.new()
    tunnel_gaps = [(a - 0.3, b + 0.3) for a, b in GALERA_TUNNELS]
    for y0, y1, kind, aisle in GALERA_SECTIONS:
        spans = [(y0 + 0.3, aisle - 0.6), (aisle + 0.6, y1 - 0.3)]
        for i in range(NUM_STEPS):
            d, z = _row(i)
            gaps = tunnel_gaps if i < TUNNEL_ROWS else []
            for a, b in spans:
                row = [s for s in seats_in_row(R_TRACK_OUT + d + STEP_D - SEAT_BACK_GAP, z, a, b) if not _in_any(s[1], gaps)]
                n = len(row) if b - a > 10.0 else 0          # napis tylko na szerszej części sekcji
                for k, s in enumerate(reversed(row)):         # k: kolumna od północy (z boiska — od lewej)
                    color = _galera_seat_color(kind, i, k, n)
                    if color:
                        (red if color == 'red' else white).append(s)
            if kind == 'top_red' and i in (3, 7, 11):
                for a, b in _minus(y0 + 0.3, y1 - 0.3, [(aisle - 0.6, aisle + 0.6)] + gaps):
                    _rail(bm_y, (R_TRACK_OUT + d + 0.15, a, z), (R_TRACK_OUT + d + 0.15, b, z), 2.0)
    red_seat = seat_material("Mat_Krzeselka_Czerwone_Galera", (0.62, 0.07, 0.09))
    place_seats(col, "Krzeselka_Galera", red_seat, red)
    place_seats(col, "Krzeselka_Galera_Biale", seat_material("Mat_Krzeselka_Biale_Galera", (0.88, 0.88, 0.86)), white)
    bmesh.ops.recalc_face_normals(bm_y, faces=bm_y.faces)
    _finish_mesh(col, bm_y, "Barierki_Zolte_Galera", [mats['yellow']])

    build_bowl_details(col, mats, red_seat, [s[3] for s in GALERA_SECTIONS])
    build_galera_tunnels(col, mats)
    build_north_sheet_fence(col, mats)
    return obj_bowl, obj_f


def _in_any(y, gaps):
    return any(a <= y <= b for a, b in gaps)


def _minus(a, b, gaps):
    """Odcinek [a, b] bez przedziałów gaps."""
    out = [(a, b)]
    for g0, g1 in gaps:
        out = [p for s0, s1 in out for p in ([(s0, s1)] if g1 <= s0 or g0 >= s1 else
                                             [q for q in ((s0, g0), (g1, s1)) if q[1] - q[0] > 0.05])]
    return out


def _galera_seat_color(kind, row, col_from_north, n_cols):
    """'red', 'white' albo None (goły beton) dla krzesełka sekcji Galery."""
    if kind == 'red':
        return 'red'
    if kind == 'top_red':
        return 'red' if row >= TOP_RED_FROM else None
    if row < BCB_WHITE_LOW or row >= BCB_WHITE_HIGH:
        return 'white'
    if kind == 'lks' and LKS_ROWS[0] <= row <= LKS_ROWS[1] and n_cols >= len(LKS_FONT[0]):
        c = col_from_north - (n_cols - len(LKS_FONT[0])) // 2
        if 0 <= c < len(LKS_FONT[0]) and LKS_FONT[LKS_ROWS[1] - row][c] == '#':
            return 'white'
    return 'red'


def _extrude_yz(bm, pts_yz, x0, x1):
    """Bryła z wielokąta w płaszczyźnie YZ wyciągniętego od x0 do x1."""
    face = bm.faces.new([bm.verts.new((x0, y, z)) for y, z in pts_yz])
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    ev = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(x1 - x0, 0.0, 0.0), verts=ev)


def build_galera_tunnels(col, mats):
    """
    Tunele wejściowe Galery (tunel_galera.png, kolorystyka_galery_oraz_budynki_tla.png): wcięcie w widownię
    od chodnika w stronę al. Unii przez pierwsze TUNNEL_ROWS rzędów, o przekroju trapezu — dno na poziomie
    chodnika, ściany pochylone na zewnątrz aż do krawędzi rzędów. W głębi wcięcia wylot przelotu pod wałem
    z Przeplatanką na nadprożu, przelot (prześwit TUNNEL_OPEN_H) prowadzi do tylnej skarpy.
    Bryły zamknięte (kolizje Octree/BVH w Three.js są jednostronne).
    """
    bm, bm_y, bm_p = bmesh.new(), bmesh.new(), bmesh.new()
    uv = bm_p.loops.layers.uv.verify()
    d_mouth, z_mouth = _row(TUNNEL_ROWS)
    x_mouth = R_TRACK_OUT + d_mouth
    treads = []
    for i in range(TUNNEL_ROWS, NUM_STEPS):
        d, z = _row(i)
        treads += [(R_TRACK_OUT + d, z), (R_TRACK_OUT + d + STEP_D, z)]
    back = STAND_BACK + 5.0                                   # stopa tylnej skarpy (build_bowl)
    slope_x = lambda z: back - 5.0 * z / STAND_H
    side = [(x_mouth, -0.05)] + treads + [(back, -0.05)]
    roof = [(x_mouth, TUNNEL_OPEN_H)] + treads + [(slope_x(TUNNEL_OPEN_H), TUNNEL_OPEN_H)]
    sl = TUNNEL_SLOPE
    for ya, yb in GALERA_TUNNELS:
        # Wcięcie: w każdym rzędzie ściany od dna do wysokości stopnia, pochylone tak, że na wysokości
        # wylotu sięgają krawędzi przęsła (ya, yb)
        for i in range(TUNNEL_ROWS):
            d, z = _row(i)
            inset = sl * (1.0 - z / z_mouth)
            x0, x1 = R_TRACK_OUT + d, R_TRACK_OUT + d + STEP_D
            _extrude_yz(bm, [(ya, -0.05), (ya + sl, -0.05), (ya + inset, z), (ya, z)], x0, x1)
            _extrude_yz(bm, [(yb - sl, -0.05), (yb, -0.05), (yb, z), (yb - inset, z)], x0, x1)
        # Za wylotem: ściany przelotu z widownią na wierzchu i strop
        _extrude_profile(bm, side, ya, ya + sl)
        _extrude_profile(bm, side, yb - sl, yb)
        _extrude_profile(bm, roof, ya + sl, yb - sl)

        # Nadproże wylotu: Przeplatanka na białym tle (tekstura 4:1, EXTEND — herb zachowuje proporcje)
        w, h = yb - ya - 2 * sl, z_mouth - TUNNEL_OPEN_H
        half_u = w / h / PRZEPLATANKA_ASPECT / 2
        x = x_mouth - 0.02
        face = bm_p.faces.new([bm_p.verts.new(p) for p in [(x, ya + sl, TUNNEL_OPEN_H), (x, ya + sl, z_mouth),
                                                         (x, yb - sl, z_mouth), (x, yb - sl, TUNNEL_OPEN_H)]])
        for loop in face.loops:
            t = (yb - sl - loop.vert.co.y) / w
            loop[uv].uv = (0.5 + (t - 0.5) * 2 * half_u, (loop.vert.co.z - TUNNEL_OPEN_H) / h)

        # Żółte barierki: wzdłuż obu krawędzi wcięcia i nad wylotem (rząd TUNNEL_ROWS)
        (d0, z0), (d9, z9) = _row(0), _row(TUNNEL_ROWS - 1)
        for ye in (ya + 0.05, yb - 0.05):
            _rail(bm_y, (R_TRACK_OUT + d0 + 0.3, ye, z0), (R_TRACK_OUT + d9 + 0.3, ye, z9), 2.0)
        _rail(bm_y, (x_mouth + 0.1, ya + 0.05, z_mouth), (x_mouth + 0.1, yb - 0.05, z_mouth), 2.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm_y, faces=bm_y.faces)
    _finish_mesh(col, bm, "Galera_Tunele", [mats['concrete']])
    _finish_mesh(col, bm_y, "Galera_Tunele_Barierki", [mats['yellow']])
    bm_p.normal_update()
    _finish_mesh(col, bm_p, "Galera_Tunele_Przeplatanka", [mats['przeplatanka']])


def _sheet_fence_path():
    """
    Punkty (x, y) ogrodzenia z blachy: prosto w poprzek za bramką północną od czoła trybuny głównej
    do łuku, dalej po czole łuku do początku prostej Galery (widok_na_trybune_z_sektora_gosci.png).
    """
    x_arc = math.sqrt((R_TRACK_OUT + 0.1) ** 2 - (SHEET_FENCE_Y - STRAIGHT_L / 2) ** 2)
    n = math.ceil((x_arc + R_TRACK_OUT) / 2.5)
    pts = [(-R_TRACK_OUT + (x_arc + R_TRACK_OUT) * k / n, SHEET_FENCE_Y) for k in range(n + 1)]
    a0 = math.degrees(math.atan2(SHEET_FENCE_Y - STRAIGHT_L / 2, x_arc))
    m = math.ceil(a0 / 4.0)
    for k in range(1, m + 1):
        (x, y), _ = _arc_point(R_TRACK_OUT + 0.1, a0 * (1 - k / m), cy=STRAIGHT_L / 2)
        pts.append((x, y))
    return pts, a0


def build_north_sheet_fence(col, mats):
    """
    Ogrodzenie z blachy trapezowej (ocynk, pionowe przetłoczenia) zamykające północny kraniec boiska:
    za nim trawa przed stopniami łuku północnego. Panele SHEET_FENCE_H na słupkach co ~2.5 m,
    zastrzały co drugi słupek od strony trybun. Blacha to dwie ściany 3 cm od siebie
    (kolizje są jednostronne); UV: 1 kafel tekstury (ambientCG CorrugatedSteel005) = SHEET_TILE_M.
    """
    pts, _ = _sheet_fence_path()
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    bm_post = bmesh.new()
    dist = 0.0
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        seg = math.hypot(x1 - x0, y1 - y0)
        nx, ny = (y1 - y0) / seg, -(x1 - x0) / seg              # normalna w poziomie
        for off, flip in [(-0.015, False), (0.015, True)]:
            c = [(x0 + nx * off, y0 + ny * off, 0.0, dist), (x1 + nx * off, y1 + ny * off, 0.0, dist + seg),
                 (x1 + nx * off, y1 + ny * off, SHEET_FENCE_H, dist + seg), (x0 + nx * off, y0 + ny * off, SHEET_FENCE_H, dist)]
            if flip:
                c = c[::-1]
            face = bm.faces.new([bm.verts.new(p[:3]) for p in c])
            for loop, p in zip(face.loops, c):
                loop[uv].uv = (p[3] / SHEET_TILE_M, p[2] / SHEET_TILE_M)   # przetłoczenia pionowe jak w teksturze
        yaw = math.atan2(y1 - y0, x1 - x0)
        _obox(bm_post, (x0, y0, SHEET_FENCE_H / 2 + 0.05), (0.08, 0.08, SHEET_FENCE_H + 0.1), yaw=yaw)
        if k % 2 == 0:
            # zastrzał od strony trybun (od środka boiska na zewnątrz): od 2/3 wysokości słupka do gruntu 1.2 m dalej
            side = 1.0 if nx * x0 + ny * y0 > 0 else -1.0
            sx, sy = nx * side, ny * side
            top = (x0, y0, SHEET_FENCE_H * 0.65)
            foot = (x0 + sx * 1.2, y0 + sy * 1.2, 0.0)
            _beam(bm_post, top, foot, 0.06, 0.06)
        dist += seg
    _obox(bm_post, (pts[-1][0], pts[-1][1], SHEET_FENCE_H / 2 + 0.05), (0.08, 0.08, SHEET_FENCE_H + 0.1))
    bm.normal_update()
    _finish_mesh(col, bm, "Ogrodzenie_Blacha_Polnoc", [mats['sheet_steel']])
    bmesh.ops.recalc_face_normals(bm_post, faces=bm_post.faces)
    _finish_mesh(col, bm_post, "Ogrodzenie_Blacha_Slupki", [mats['metal']])


def build_bowl_details(col, mats, red_seat, galera_aisles):
    """
    Wyposażenie podkowy ze zdjęć 2010–2012 (widok_z_galery.jpg, widok_na_zegar_u2.png): krzesełka
    i goły beton łuku południowego, żółte barierki, niskie ogrodzenie łuków, ślad dawnej bieżni, bandy na koronie.
    Barierki i ogrodzenie to bryły (kolizje Octree są jednostronne).
    """
    yellow = mats['yellow']

    # Krzesełka łuku południowego (wschodnia połowa): 4 bloki rozdzielone betonowymi zejściami
    # SOUTH_AISLE_W, w każdym bloku krótkie żółte barierki w rzędach SOUTH_BLOCK_RAIL_ROWS
    # (w tych rzędach pod barierką bez krzesełek). Krzesełka skierowane do środka łuku.
    bm_y = bmesh.new()
    a0, a1 = SOUTH_SEAT_ARC
    cuts = [a0] + list(SOUTH_AISLES) + [a1]
    seats = []
    for i in range(NUM_STEPS):
        d, z = _row(i)
        r = R_TRACK_OUT + d + STEP_D - SEAT_BACK_GAP
        half_gap = math.degrees(SOUTH_AISLE_W / 2 / r)
        for b0, b1 in zip(cuts, cuts[1:]):
            lo, hi = b0 + (half_gap if b0 != a0 else 0.0), b1 - (half_gap if b1 != a1 else 0.0)
            mid, rail_half = (b0 + b1) / 2, math.degrees(SOUTH_BLOCK_RAIL_LEN / 2 / r)
            n = int(math.radians(hi - lo) * r / SEAT_PITCH)
            for k in range(n):
                ang = lo + (k + 0.5) * (hi - lo) / n
                if i in SOUTH_BLOCK_RAIL_ROWS and abs(ang - mid) < rail_half + 0.4:
                    continue
                (x, y), a = _arc_point(r, ang)
                seats.append((x, y, z, a))
            if i in SOUTH_BLOCK_RAIL_ROWS:
                rr = R_TRACK_OUT + d + 0.35
                arc = [_arc_point(rr, mid - rail_half + 2 * rail_half * t / 4)[0] for t in range(5)]
                for (xa, ya), (xb, yb) in zip(arc, arc[1:]):
                    _beam(bm_y, (xa, ya, z + 1.0), (xb, yb, z + 1.0))
                for xa, ya in (arc[0], arc[-1]):
                    _beam(bm_y, (xa, ya, z), (xa, ya, z + 1.0))
    place_seats(col, "Krzeselka_Luk_Poludniowy", red_seat, seats)

    # Zachodnia połowa łuku: goły beton z poprzecznymi żółtymi barierkami (odcinki 3° z przerwą co piąty)
    seg_deg = 3.0
    for i_rail in SOUTH_CONCRETE_RAIL_ROWS:
        d, z = _row(i_rail)
        r = R_TRACK_OUT + d + 0.15
        ang = SOUTH_CONCRETE_ARC[0]
        while ang + seg_deg <= SOUTH_CONCRETE_ARC[1]:
            if int((ang - SOUTH_CONCRETE_ARC[0]) / seg_deg) % 5 != 4:
                (x, y), a = _arc_point(r, ang + seg_deg / 2)
                _obox(bm_y, (x, y, z + 1.0), (0.05, 2 * r * math.sin(math.radians(seg_deg / 2)), 0.05), yaw=a)
                (px, py), _ = _arc_point(r, ang + 0.2)
                _obox(bm_y, (px, py, z + 0.5), (0.05, 0.05, 1.0))
            ang += seg_deg

    # Łuk północny: barierki U (poręcz na 1 m, dwa słupki), co drugi rząd barierek przesunięty o pół rozstawu
    for n_row, i_rail in enumerate(NORTH_RAIL_ROWS):
        d, z = _row(i_rail)
        r = R_TRACK_OUT + d + 0.15
        seg, period = math.degrees(NORTH_RAIL_LEN / r), math.degrees(NORTH_RAIL_PERIOD / r)
        ang = NORTH_ARC[0] + (period / 2 if n_row % 2 else 0.0)
        while ang + seg <= NORTH_ARC[1]:
            pts = [_arc_point(r, ang + seg * t / 3, STRAIGHT_L / 2)[0] for t in range(4)]
            for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                _beam(bm_y, (xa, ya, z + 1.0), (xb, yb, z + 1.0))
            for xa, ya in (pts[0], pts[-1]):
                _beam(bm_y, (xa, ya, z), (xa, ya, z + 1.0))
            ang += period

    # Żółte poręcze przy przejściach Galery (wzdłuż spadku, przy krawędzi sektora)
    run = math.hypot(STEP_D, STEP_H)
    pitch = -math.atan2(STEP_H, STEP_D)
    for a in galera_aisles:
        y = a + 0.52
        for i in range(NUM_STEPS - 1):
            d, z = _row(i)
            _obox(bm_y, (R_TRACK_OUT + d + STEP_D, y, z + STEP_H / 2 + 1.0), (run, 0.05, 0.05), pitch=pitch)
            if i % 2 == 0:
                _obox(bm_y, (R_TRACK_OUT + d + 0.55, y, z + 0.5), (0.05, 0.05, 1.0))
    bmesh.ops.recalc_face_normals(bm_y, faces=bm_y.faces)
    _finish_mesh(col, bm_y, "Barierki_Zolte", [yellow])

    # Niskie ogrodzenie łuków: słupki co ~2.5 m na przemian czerwone i białe, dwie poręcze.
    # Na łuku północnym przy Galerze zamiast niego blacha (build_north_sheet_fence).
    _, sheet_arc_deg = _sheet_fence_path()
    bm_lf = bmesh.new()
    path = stadium_path(R_TRACK_OUT + 0.15, BOWL_ANGLE_N, -BOWL_ANGLE_S, arc_step_deg=3.0)
    k = 0
    for (x0, y0, nx0, ny0), (x1, y1, nx1, ny1) in zip(path, path[1:]):
        if abs(ny0) < 1e-6 and abs(ny1) < 1e-6:     # prosta Galery ma wysokie ogrodzenie
            continue
        if y0 > 0 and math.degrees(math.atan2(y0 - STRAIGHT_L / 2, x0)) < sheet_arc_deg - 1e-6 and x0 > 0:
            continue
        if y0 > STRAIGHT_L / 2 and GUEST_ARC[0] <= math.degrees(math.atan2(y0 - STRAIGHT_L / 2, x0)) <= GUEST_ARC[1]:
            continue                                # sektor gości ma wysokie ogrodzenie (build_bowl)
        yaw = math.atan2(y1 - y0, x1 - x0) - math.pi / 2
        seg = math.hypot(x1 - x0, y1 - y0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        for h in (0.6, LOW_FENCE_H - 0.03):
            _obox(bm_lf, (mx, my, h), (0.05, seg, 0.05), yaw=yaw)
        post = _obox(bm_lf, (x0, y0, LOW_FENCE_H / 2), (0.09, 0.09, LOW_FENCE_H), yaw=yaw)
        for f in {f for v in post['verts'] for f in v.link_faces}:
            f.material_index = k % 2
        k += 1
    _finish_mesh(col, bm_lf, "Ogrodzenie_Niskie_Luki", [mats['lks_red'], mats['goal_white']])

    # Ślad dawnej bieżni: wydeptany, ciemny pas żużlu w trawie (pełna pętla)
    trace = _flat("Mat_Slad_Biezni", (0.075, 0.065, 0.055), 0.95)
    bm_t = bmesh.new()
    inner = stadium_path(42.7, 180.0, -180.0, close_west=True)
    outer = stadium_path(43.8, 180.0, -180.0, close_west=True)
    vi = [bm_t.verts.new((x, y, 0.035)) for x, y, _, _ in inner]
    vo = [bm_t.verts.new((x, y, 0.035)) for x, y, _, _ in outer]
    for j in range(len(vi)):
        bm_t.faces.new([vi[j], vo[j], vo[(j + 1) % len(vo)], vi[(j + 1) % len(vi)]])
    _finish_mesh(col, bm_t, "Slad_Biezni", [trace])

    # Bandy reklamowe na słupach na koronie łuku południowego (atlas ads_crown.png: 4 wiersze 4:1)
    bm_ad = bmesh.new()
    uv = bm_ad.loops.layers.uv.verify()
    r = STAND_BACK - 0.4
    for ang, row in SOUTH_ADS:
        (x, y), a = _arc_point(r, ang)
        board = _obox(bm_ad, (x, y, STAND_H + 3.05), (0.08, 3.6, 0.9), yaw=a)
        v0, v1 = 1.0 - (row + 1) / 4.0, 1.0 - row / 4.0
        tangent = mathutils.Vector((-math.sin(a), math.cos(a), 0.0))
        radial = mathutils.Vector((math.cos(a), math.sin(a), 0.0))
        for f in {f for v in board['verts'] for f in v.link_faces}:
            front = f.normal.dot(radial) < -0.9                     # lico skierowane do boiska
            for loop in f.loops:
                p = loop.vert.co - mathutils.Vector((x, y, STAND_H + 3.05))
                if front:
                    u = 0.5 - p.dot(tangent) / 3.6                  # od lewej patrząc z boiska
                    v = v0 + (p.z / 0.9 + 0.5) * (v1 - v0)
                    loop[uv].uv = (u, v)
                else:
                    loop[uv].uv = (0.004, v0 + 0.004)               # biały margines atlasu
        for side in (-1.3, 1.3):
            sx, sy = x + side * tangent.x, y + side * tangent.y
            _obox(bm_ad, (sx, sy, STAND_H + 1.3), (0.1, 0.1, 2.6), yaw=a)
    _finish_mesh(col, bm_ad, "Bandy_Korona_Luk", [mats['ads_crown']])


def build_temporary_south_stand(col, mats):
    """
    Trybuna tymczasowa (TEMP_*) i piłkochwyt przed nią (BALL_NET_*). Pomosty rzędów i podstopnie to płyty
    stalowe, pod nimi rusztowanie: stojaki co TEMP_BAY na każdej krawędzi rzędu, zastrzały na przedniej
    i tylnej ścianie. Krzesełka patrzą na północ, na boisko; przejścia TEMP_AISLES bez krzesełek, ze stopniem
    wejściowym z gruntu.
    """
    x0, x1 = TEMP_STAND_X
    yf = TEMP_STAND_FRONT_Y
    edge = lambda i: yf - i * TEMP_ROW_D                     # krawędź rzędu i (i = 0: czoło trybuny)
    deck = lambda i: TEMP_DECK0 + i * TEMP_ROW_H             # wysokość pomostu rzędu i
    yb, z_top = edge(TEMP_ROWS), deck(TEMP_ROWS - 1)

    bm_deck, bm_frame, bm_green, bm_roof = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    for i in range(TEMP_ROWS):
        _obox(bm_deck, ((x0 + x1) / 2, (edge(i) + edge(i + 1)) / 2, deck(i) - 0.04), (x1 - x0, TEMP_ROW_D, 0.08))
        z_low = deck(i - 1) if i else 0.0
        _obox(bm_deck, ((x0 + x1) / 2, edge(i) - 0.015, (z_low + deck(i)) / 2), (x1 - x0, 0.03, deck(i) - z_low))
    for xa in TEMP_AISLES:                                   # stopień wejściowy z gruntu na pierwszy pomost
        _obox(bm_deck, (xa, yf + 0.2, deck(0) / 4), (TEMP_AISLE_W, 0.4, deck(0) / 2))

    n_bays = round((x1 - x0) / TEMP_BAY)
    xs = [x0 + 0.1 + k * (x1 - x0 - 0.2) / n_bays for k in range(n_bays + 1)]
    for k, x in enumerate(xs):
        for i in range(TEMP_ROWS + 1):
            top = deck(min(i, TEMP_ROWS - 1)) - 0.08
            _beam(bm_frame, (x, edge(i) - 0.05, 0.0), (x, edge(i) - 0.05, top), 0.05, 0.05)
        if k < n_bays:
            for i in (0, TEMP_ROWS):
                top = deck(min(i, TEMP_ROWS - 1)) - 0.1
                a, b = (x, xs[k + 1]) if k % 2 else (xs[k + 1], x)
                _beam(bm_frame, (a, edge(i) - 0.05, 0.1), (b, edge(i) - 0.05, top), 0.04, 0.04)
    _rail(bm_frame, (x0, yf + 0.05, deck(0)), (x1, yf + 0.05, deck(0)), 2.5)
    _rail(bm_frame, (x0, yb + 0.05, z_top), (x1, yb + 0.05, z_top), 2.5)
    for x in (x0 + 0.05, x1 - 0.05):
        _rail(bm_frame, (x, yf, deck(0)), (x, yb, z_top), 1.6)

    zf, zb = TEMP_ROOF_Z
    n_posts = round((x1 - x0) / TEMP_ROOF_POST_EVERY)
    for k in range(n_posts + 1):
        x = x0 + 0.1 + k * (x1 - x0 - 0.2) / n_posts
        _beam(bm_green, (x, yf - 0.1, deck(0)), (x, yf - 0.1, zf), 0.12, 0.12)
        _beam(bm_green, (x, yb + 0.1, z_top), (x, yb + 0.1, zb), 0.12, 0.12)
    _beam(bm_green, (x0, yf - 0.1, zf - 0.1), (x1, yf - 0.1, zf - 0.1), 0.12, 0.2)
    _beam(bm_green, (x0, yb + 0.1, zb - 0.1), (x1, yb + 0.1, zb - 0.1), 0.12, 0.2)
    over, k = 0.6, (zf - zb) / (yf - yb)                   # okap od boiska, spadek dachu
    top_f, top_b = (yf + over, zf + over * k), (yb - 0.3, zb - 0.3 * k)
    _extrude_yz(bm_roof, [top_f, top_b, (top_b[0], top_b[1] - 0.08), (top_f[0], top_f[1] - 0.08)], x0 - 0.3, x1 + 0.3)
    bmesh.ops.recalc_face_normals(bm_roof, faces=bm_roof.faces)

    seats = []
    gaps = [(a - TEMP_AISLE_W / 2, a + TEMP_AISLE_W / 2) for a in TEMP_AISLES]
    for i in range(TEMP_ROWS):
        y = edge(i + 1) + SEAT_BACK_GAP
        x = x0 + 0.5
        while x < x1 - 0.4:
            if not any(a - 0.25 < x < b + 0.25 for a, b in gaps):
                seats.append((x, y, deck(i), -math.pi / 2))
            x += SEAT_PITCH

    _finish_mesh(col, bm_deck, "Trybuna_Tymczasowa_Pomosty", [mats['metal']])
    _finish_mesh(col, bm_frame, "Trybuna_Tymczasowa_Rusztowanie", [mats['metal']])
    _finish_mesh(col, bm_green, "Trybuna_Tymczasowa_Slupy", [mats['steel_green']])
    _finish_mesh(col, bm_roof, "Trybuna_Tymczasowa_Dach", [mats['roof_dark']])
    place_seats(col, "Krzeselka_Trybuna_Tymczasowa", seat_material("Mat_Krzeselka_Tymczasowe", (0.62, 0.07, 0.09)), seats)

    # Piłkochwyt: siatka od gruntu do liny, lina ugięta między słupami; UV 1 kafel = 1 m
    bm_net, bm_posts = bmesh.new(), bmesh.new()
    uv = bm_net.loops.layers.uv.verify()
    nx0, nx1 = BALL_NET_X
    n = round((nx1 - nx0) / BALL_NET_POST_EVERY)
    px = [nx0 + k * (nx1 - nx0) / n for k in range(n + 1)]
    for xa, xb in zip(px, px[1:]):
        steps = 6
        cols = []
        for j in range(steps + 1):
            t = j / steps
            x = xa + t * (xb - xa)
            cols.append((x, BALL_NET_H - 0.1 - BALL_NET_SAG * 4 * t * (1 - t)))
        for (xa_, za), (xb_, zb_) in zip(cols, cols[1:]):
            c = [(xa_, 0.1), (xb_, 0.1), (xb_, zb_), (xa_, za)]
            face = bm_net.faces.new([bm_net.verts.new((x, BALL_NET_Y, z)) for x, z in c])
            for loop, (x, z) in zip(face.loops, c):
                loop[uv].uv = (x, z)
    for x in px:
        _beam(bm_posts, (x, BALL_NET_Y - 0.06, 0.0), (x, BALL_NET_Y - 0.06, BALL_NET_H), 0.1, 0.1)
    _finish_mesh(col, bm_net, "Pilkochwyt_Siatka", [mats['ball_net']])
    _finish_mesh(col, bm_posts, "Pilkochwyt_Slupy", [mats['metal']])


def _flat(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def build_fan_banners(col, mats):
    """
    Tworzy kibicowskie banery i historyczne graffiti wzdłuż prostej wschodniej ("Galera").
    """
    bm = bmesh.new()
    BX = R_TRACK_OUT - 0.03  # przed ogrodzeniem Galery (banery wieszane na siatce)
    BY_START = -36.0
    BY_END = 36.0
    BZ_BOT = 0.2
    BZ_TOP = 1.3
    
    # Czoło od strony boiska (widok z murawy i Trybuny Głównej ku Galerze)
    pts_front = [
        (BX - 0.02, BY_END,   BZ_BOT),
        (BX - 0.02, BY_START, BZ_BOT),
        (BX - 0.02, BY_START, BZ_TOP),
        (BX - 0.02, BY_END,   BZ_TOP)
    ]
    f_front = bm.faces.new([bm.verts.new(p) for p in pts_front])
    uv_layer = bm.loops.layers.uv.verify()
    for loop in f_front.loops:
        u = (BY_END - loop.vert.co.y) / (BY_END - BY_START)
        v = (loop.vert.co.z - BZ_BOT) / (BZ_TOP - BZ_BOT)
        loop[uv_layer].uv = (u, v)

    # Tył od strony korony trybuny Galera
    pts_back = [
        (BX + 0.02, BY_START, BZ_BOT),
        (BX + 0.02, BY_END,   BZ_BOT),
        (BX + 0.02, BY_END,   BZ_TOP),
        (BX + 0.02, BY_START, BZ_TOP)
    ]
    f_back = bm.faces.new([bm.verts.new(p) for p in pts_back])
    for loop in f_back.loops:
        u = (loop.vert.co.y - BY_START) / (BY_END - BY_START)
        v = (loop.vert.co.z - BZ_BOT) / (BZ_TOP - BZ_BOT)
        loop[uv_layer].uv = (u, v)
        
    mesh_b = bpy.data.meshes.new("Banery_Kibicowskie_Galera_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh_b)
    bm.free()
    
    obj_b = bpy.data.objects.new("Banery_Kibicowskie_Galera", mesh_b)
    if mats and 'fan_banners' in mats:
        obj_b.data.materials.append(mats['fan_banners'])
    col.objects.link(obj_b)
    return obj_b


def build_scoreboard(col, mats):
    """
    Historyczna tablica wyników z zegarem stojąca na KORONIE KRÓTKIEJ TRYBUNY OD POŁUDNIA.
    Skierowana na północ (+Y), twarzą do murawy i Trybuny Głównej.
    Czoło tablicy posiada autentyczną teksturę ze zdjęcia archiwalnego (z zegarem, matrycą i napisem).
    """
    BOARD_W = 20.0
    BOARD_H = 7.5
    BOARD_D = 1.2
    CLEARANCE = 4.2 # słupy nośne nad wałem
    
    # 1. Konstrukcja i skrzynia tablicy
    bm_board = bmesh.new()
    uv_layer = bm_board.loops.layers.uv.verify()
    
    # 2 słupy nośne
    COL_R = 0.50
    for sy in [-BOARD_W/3.5, BOARD_W/3.5]:
        c = bmesh.ops.create_cone(
            bm_board,
            cap_ends=True,
            segments=12,
            radius1=COL_R,
            radius2=COL_R,
            depth=CLEARANCE + 1.0
        )
        bmesh.ops.translate(bm_board, vec=(0.0, sy, (CLEARANCE + 1.0)/2.0), verts=c['verts'])

    # Skrzynia tablicy (czoło w -X w lokalnym układzie)
    box = bmesh.ops.create_cube(bm_board, size=1.0)
    bmesh.ops.scale(bm_board, vec=(BOARD_D, BOARD_W, BOARD_H), verts=box['verts'])
    bmesh.ops.translate(bm_board, vec=(0.0, 0.0, CLEARANCE + BOARD_H/2.0), verts=box['verts'])

    # Mapowanie UV i indeksy materiałów dla skrzyni tablicy i słupów
    for f in bm_board.faces:
        # Płyta czołowa skrzyni skierowana w stronę murawy (-X)
        if f.normal.x < -0.8 and f.calc_center_median().z > CLEARANCE:
            f.material_index = 1 # Mat_Board_Historic
            for loop in f.loops:
                u = (BOARD_W / 2.0 - loop.vert.co.y) / BOARD_W
                v = (loop.vert.co.z - CLEARANCE) / BOARD_H
                loop[uv_layer].uv = (u, v)
        else:
            f.material_index = 0 # Mat_Board_Dark (stalowa obudowa i słupy)
            for loop in f.loops:
                loop[uv_layer].uv = (0.1, 0.1)

    mesh_board = bpy.data.meshes.new("Tablica_Wynikow_Mesh")
    bm_board.normal_update()
    bm_board.to_mesh(mesh_board)
    bm_board.free()

    obj_board = bpy.data.objects.new("Tablica_Wynikow_Zegar", mesh_board)
    # Pozycja: na koronie krótkiej trybuny od południa (X = 0.0m, Y = -110.5m, Z = 6.8m)
    obj_board.location = (0.0, -110.5, 6.8)
    # Obrót o -90° wokół Z (normalna czoła z -X obraca się w stronę +Y ku murawie)
    obj_board.rotation_euler = (0.0, 0.0, math.radians(-90))
    
    if mats and 'board_dark' in mats:
        obj_board.data.materials.append(mats['board_dark'])       # Index 0
    if mats and 'board_historic' in mats:
        obj_board.data.materials.append(mats['board_historic'])   # Index 1
        
    col.objects.link(obj_board)
    return obj_board

if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import sys, os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from build_grandstand import create_materials
    
    mats = create_materials()
    col = bpy.data.collections.new("Test_Bowl")
    bpy.context.scene.collection.children.link(col)
    
    build_pitch_and_track(col, mats)
    build_bowl(col, mats)
    build_scoreboard(col, mats)
    
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bowl_v2_test.blend"))
    print("Zapisano test korony z bieznią i zegarem vis a vis.")
