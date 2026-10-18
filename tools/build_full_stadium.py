"""
Generowanie kompletnego stadionu ŁKS Łódź ("Estadio da Gruz", 1969-2012):
1. Trybuna Główna (Zachodnia) arch. Wyżnikiewicza i Szklarka:
   - 14 przęseł modułowych (130 m) z 15 kablobetonowymi dźwigarami
   - Brutalistyczne ukośne odciągi od strony zachodniej (Atlas Arena)
   - Pawilon zaplecza z wstęgowymi oknami
   - Otwarta ku górze korona o realistycznej wysokości 14 m (bez dachu szczytowego)
   - Sektor dolny z niskim daszkiem blaszanym (sektor VIP / trybuna kryta z białą fasadą)
   - Słupki oświetleniowe wzdłuż szczytu korony
2. Korona Stadionu (Podkowa):
   - Murawa 105 x 68 m z bramkami piłkarskimi
   - Bieżnia żużlowa 400 m biegnąca w całości POMIĘDZY murawą a trybunami (nie zachodzi za Main Stand)
   - Mur oporowy (1.5 m) ze stalowym ogrodzeniem na czole podkowy — bez fosy (docs/zrodla.md)
   - Wały ziemne z 20 betonowymi stopniami
   - Historyczna tablica wyników z zegarem na łuku południowym
3. Cztery Maszty Oświetleniowe (Jupitery z 1970 r., h=46m):
   - Konstrukcja 3-nożna o przekroju trójkątnym zbieżnym ku górze
   - Głowica w kształcie ODWRÓCONEGO TRAPEZU (węższa podstawa na dole, szersza na górze)
   - 45 reflektorów pochylonych w dół o 28° w stronę murawy
4. Otoczenie wg ortofotomapy 2013: teren, plac, al. Unii, tory, Atlas Arena, drzewa
5. Eksport do formatu GLB pod Three.js
"""

import bpy
import bmesh
import mathutils
import math
import sys
import os

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.append(TOOLS_DIR)

from build_grandstand import (
    create_materials, build_grandstand, lower_seat_rows, lower_seat_removed,
    TOTAL_LENGTH_Y as GRANDSTAND_LENGTH, NUM_BAYS, BAY_WIDTH_Y
)
from build_seats import place_seats, seat_material, seats_in_row
from build_floodlight_mast import build_floodlight_mast
from build_surroundings import build_surroundings
from bake_lighting import bake_ambient_occlusion
from build_horseshoe_bowl import (
    build_pitch_and_track,
    build_pitch_lines,
    build_bowl,
    build_fan_banners,
    build_scoreboard,
    build_temporary_south_stand
)

ROOT = os.path.dirname(TOOLS_DIR)
GRANDSTAND_CENTER_Y = 3.0  # przesunięcie środka trybuny głównej na północ (ortofotomapa 2013)
UV_METERS_PER_UNIT = 4.0  # ta sama konwencja co UV daszków w build_grandstand.py


def prepare_meshes_for_export():
    """
    Ostatni przebieg przed eksportem GLB:
    - usuwa zdegenerowane trójkąty (zerowa normalna psuje kolizje Octree w Three.js),
    - nadaje UV metodą box projection w przestrzeni świata siatkom bez UV — bez tego
      tekstury PBR (beton, blacha) próbkowały jeden teksel, a exporter zapisywał texCoord: -1.
    """
    bpy.context.view_layer.update()
    done = set()
    for obj in bpy.context.scene.objects:
        # siatki współdzielone (drzewa) przetwarzamy raz
        if obj.type != 'MESH' or obj.data.name in done:
            continue
        done.add(obj.data.name)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)

        if not obj.data.uv_layers:
            uv = bm.loops.layers.uv.new("UVMap")
            mw = obj.matrix_world
            rot = mw.to_3x3()
            for face in bm.faces:
                n = rot @ face.normal
                ax = max(range(3), key=lambda k: abs(n[k]))
                a, b = [(1, 2), (0, 2), (0, 1)][ax]
                for loop in face.loops:
                    co = mw @ loop.vert.co
                    loop[uv].uv = (co[a] / UV_METERS_PER_UNIT, co[b] / UV_METERS_PER_UNIT)

        bm.to_mesh(obj.data)
        bm.free()


def add_cylinder(bm, p1, p2, radius=0.06, segments=12):
    v1 = mathutils.Vector(p1)
    v2 = mathutils.Vector(p2)
    diff = v2 - v1
    length = diff.length
    if length < 1e-4:
        return
    center = (v1 + v2) / 2.0
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=length)
    dir_vec = diff.normalized()
    z_axis = mathutils.Vector((0, 0, 1))
    rot_quat = z_axis.rotation_difference(dir_vec)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot_quat.to_matrix(), verts=res['verts'])
    bmesh.ops.translate(bm, vec=center, verts=res['verts'])

def build_goals(col, mats):
    """Bramki piłkarskie (białe ramy, siatki w pasy biało-czerwono-białe). Ławki rezerwowych: build_grandstand.py."""
    POST_R = 0.06
    PIPE_R = 0.035
    mat_frame = mats.get('goal_white', mats.get('fascia'))
    mat_net = mats.get('goal_net', mats.get('fascia'))

    for sign_y in [-1, 1]:
        goal_y = sign_y * 52.5

        # 1. Biała rama bramki (słupki, poprzeczka, tylne odciągi i rama dolna)
        bm_frame = bmesh.new()
        # Słupki pionowe
        add_cylinder(bm_frame, (-3.66, goal_y, 0.0), (-3.66, goal_y, 2.44), radius=POST_R, segments=12)
        add_cylinder(bm_frame, ( 3.66, goal_y, 0.0), ( 3.66, goal_y, 2.44), radius=POST_R, segments=12)
        # Poprzeczka
        add_cylinder(bm_frame, (-3.66 - POST_R, goal_y, 2.44), (3.66 + POST_R, goal_y, 2.44), radius=POST_R, segments=12)
        # Górne rury poziome do tyłu (głębokość dachu siatki 1.0 m)
        add_cylinder(bm_frame, (-3.66, goal_y, 2.44), (-3.66, goal_y + sign_y * 1.0, 2.44), radius=PIPE_R, segments=8)
        add_cylinder(bm_frame, ( 3.66, goal_y, 2.44), ( 3.66, goal_y + sign_y * 1.0, 2.44), radius=PIPE_R, segments=8)
        add_cylinder(bm_frame, (-3.66, goal_y + sign_y * 1.0, 2.44), (3.66, goal_y + sign_y * 1.0, 2.44), radius=PIPE_R, segments=8)
        # Tylne ukośne odciągi do podłoża (głębokość przy ziemi 2.0 m)
        add_cylinder(bm_frame, (-3.66, goal_y + sign_y * 2.0, 0.03), (-3.66, goal_y + sign_y * 1.0, 2.44), radius=PIPE_R, segments=8)
        add_cylinder(bm_frame, ( 3.66, goal_y + sign_y * 2.0, 0.03), ( 3.66, goal_y + sign_y * 1.0, 2.44), radius=PIPE_R, segments=8)
        # Przyziemna rama stabilizująca
        add_cylinder(bm_frame, (-3.66, goal_y, 0.03), (-3.66, goal_y + sign_y * 2.0, 0.03), radius=PIPE_R, segments=8)
        add_cylinder(bm_frame, ( 3.66, goal_y, 0.03), ( 3.66, goal_y + sign_y * 2.0, 0.03), radius=PIPE_R, segments=8)
        add_cylinder(bm_frame, (-3.66, goal_y + sign_y * 2.0, 0.03), (3.66, goal_y + sign_y * 2.0, 0.03), radius=PIPE_R, segments=8)

        mesh_frame = bpy.data.meshes.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Rama_Mesh")
        bm_frame.normal_update()
        bm_frame.to_mesh(mesh_frame)
        bm_frame.free()

        obj_frame = bpy.data.objects.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Rama", mesh_frame)
        if mat_frame:
            obj_frame.data.materials.append(mat_frame)
        col.objects.link(obj_frame)

        # 2. Siatka bramki w pasy biało-czerwono-białe (ŁKS / Ajax)
        bm_net = bmesh.new()
        uv_layer = bm_net.loops.layers.uv.verify()

        # Profil siatki: dach (od poprzeczki do tyłu) i opadający tył
        profile = [
            (0.0, 2.44, 1.0),
            (sign_y * 1.0, 2.44, 0.72),
            (sign_y * 1.5, 1.22, 0.36),
            (sign_y * 2.0, 0.0, 0.0)
        ]

        # Podział szerokości na 6 segmentów (pas lewy biały, pas środkowy czerwony, pas prawy biały)
        N_X = 6
        x_steps = [-3.66 + i * (7.32 / N_X) for i in range(N_X + 1)]

        grid = []
        for p_idx, (y_off, z_h, v_val) in enumerate(profile):
            row = []
            py = goal_y + y_off
            for i, x_val in enumerate(x_steps):
                v = bm_net.verts.new((x_val, py, z_h))
                row.append((v, x_val, v_val))
            grid.append(row)

        # Tworzenie czworokątów dachu i ściany tylnej z mapowaniem UV
        for j in range(len(profile) - 1):
            for i in range(N_X):
                v00, x0, v_top = grid[j][i]
                v10, x1, _     = grid[j][i+1]
                v11, _,  v_bot = grid[j+1][i+1]
                v01, _,  _     = grid[j+1][i]

                # Widok od strony boiska w stronę bramki:
                # Bramka północna (+Y): lewa strona to -X, prawa to +X
                # Bramka południowa (-Y): lewa strona to +X, prawa to -X
                if sign_y > 0:
                    u0 = (x0 + 3.66) / 7.32
                    u1 = (x1 + 3.66) / 7.32
                    face = bm_net.faces.new([v00, v10, v11, v01])
                    for loop in face.loops:
                        if loop.vert == v00:
                            loop[uv_layer].uv = (u0, v_top)
                        elif loop.vert == v10:
                            loop[uv_layer].uv = (u1, v_top)
                        elif loop.vert == v11:
                            loop[uv_layer].uv = (u1, v_bot)
                        elif loop.vert == v01:
                            loop[uv_layer].uv = (u0, v_bot)
                else:
                    u0 = (3.66 - x0) / 7.32
                    u1 = (3.66 - x1) / 7.32
                    face = bm_net.faces.new([v00, v01, v11, v10])
                    for loop in face.loops:
                        if loop.vert == v00:
                            loop[uv_layer].uv = (u0, v_top)
                        elif loop.vert == v01:
                            loop[uv_layer].uv = (u0, v_bot)
                        elif loop.vert == v11:
                            loop[uv_layer].uv = (u1, v_bot)
                        elif loop.vert == v10:
                            loop[uv_layer].uv = (u1, v_top)

        # Boki siatki (oba białe, zmapowane do białego pasa siatki w U in [0.05, 0.33])
        for side_x in [-3.66, 3.66]:
            col_idx = 0 if side_x < 0 else N_X
            vs_fb = bm_net.verts.new((side_x, goal_y, 0.0))
            vs_ft = grid[0][col_idx][0]
            vs_bt = grid[1][col_idx][0]
            vs_bm = grid[2][col_idx][0]
            vs_bb = grid[3][col_idx][0]
            vs_g_mid = bm_net.verts.new((side_x, goal_y + sign_y * 1.0, 0.0))

            f_side1 = bm_net.faces.new([vs_fb, vs_ft, vs_bt, vs_g_mid])
            for l in f_side1.loops:
                if l.vert == vs_fb:
                    l[uv_layer].uv = (0.05, 0.0)
                elif l.vert == vs_ft:
                    l[uv_layer].uv = (0.05, 1.0)
                elif l.vert == vs_bt:
                    l[uv_layer].uv = (0.20, 1.0)
                elif l.vert == vs_g_mid:
                    l[uv_layer].uv = (0.20, 0.0)

            vs_g_slope = bm_net.verts.new((side_x, goal_y + sign_y * 1.5, 0.0))
            f_side2 = bm_net.faces.new([vs_g_mid, vs_bt, vs_bm, vs_g_slope])
            for l in f_side2.loops:
                if l.vert == vs_g_mid:
                    l[uv_layer].uv = (0.20, 0.0)
                elif l.vert == vs_bt:
                    l[uv_layer].uv = (0.20, 1.0)
                elif l.vert == vs_bm:
                    l[uv_layer].uv = (0.28, 0.5)
                elif l.vert == vs_g_slope:
                    l[uv_layer].uv = (0.28, 0.0)

            f_side3 = bm_net.faces.new([vs_g_slope, vs_bm, vs_bb])
            for l in f_side3.loops:
                if l.vert == vs_g_slope:
                    l[uv_layer].uv = (0.28, 0.0)
                elif l.vert == vs_bm:
                    l[uv_layer].uv = (0.28, 0.5)
                elif l.vert == vs_bb:
                    l[uv_layer].uv = (0.33, 0.0)

        mesh_net = bpy.data.meshes.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Siatka_Mesh")
        bm_net.normal_update()
        bm_net.to_mesh(mesh_net)
        bm_net.free()

        obj_net = bpy.data.objects.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Siatka", mesh_net)
        if mat_net:
            obj_net.data.materials.append(mat_net)
        col.objects.link(obj_net)
        obj_net.parent = obj_frame


def assemble_full_stadium():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = create_materials()
    
    # Kolekcje główne
    root_col = bpy.data.collections.new("Estadio_da_Gruz_1969_2012")
    bpy.context.scene.collection.children.link(root_col)
    
    col_pitch = bpy.data.collections.new("01_Murawa_i_Bieznia")
    col_grandstand = bpy.data.collections.new("02_Trybuna_Glowna_Zachodnia")
    col_bowl = bpy.data.collections.new("03_Korona_Podkowa")
    col_jupiters = bpy.data.collections.new("04_Jupitery_Maszty")
    col_surroundings = bpy.data.collections.new("05_Otoczenie")

    for c in [col_pitch, col_grandstand, col_bowl, col_jupiters, col_surroundings]:
        root_col.children.link(c)
        
    print("--- 1. Generowanie Murawy, Linii Boiska, Bieżni i Bramek ---")
    build_pitch_and_track(col_pitch, mats)
    build_pitch_lines(col_pitch, mats)
    build_goals(col_pitch, mats)
    
    print("--- 2. Generowanie Korony (Wały, Mur z Ogrodzeniem, Banery Kibicowskie, Zegar od Południa) ---")
    build_bowl(col_bowl, mats)
    build_fan_banners(col_bowl, mats)
    build_scoreboard(col_bowl, mats)
    build_temporary_south_stand(col_bowl, mats)
    
    print("--- 3. Generowanie Trybuny Głównej (Zachodniej) ---")
    build_grandstand(col_grandstand, mats)
    
    # Nadrzędny Empty dla Trybuny Głównej
    empty_grandstand = bpy.data.objects.new("Trybuna_Glowna_Root", None)
    col_grandstand.objects.link(empty_grandstand)
    
    for obj in col_grandstand.objects:
        if obj != empty_grandstand and obj.parent is None:
            obj.parent = empty_grandstand
            
    # Ustawienie pozycji Trybuny Głównej po zachodniej stronie:
    # Obrót o 180° wokół Z (front do murawy na wschód, tył na zachód w stronę parku)
    empty_grandstand.rotation_euler = (0.0, 0.0, math.radians(180))
    # Pozycjonowanie: czoło dolnych stopni (X_local = 0.0) przy zewnętrznej krawędzi bieżni X = -45 m
    # (ortofotomapa: czoło daszku sektora dolnego -44.7 m). Środek trybuny ~3 m na północ od osi
    # poprzecznej boiska (nakładka modelu na ortofotomapę, tools/add_ortho_reference.py).
    empty_grandstand.location = (-45.0, GRANDSTAND_LENGTH / 2.0 + GRANDSTAND_CENTER_Y, 0.0)

    # Krzesełka sektora dolnego: czerwone pod czerwonym daszkiem (przęsła 6..10), białe w pozostałych
    red, white = [], []
    for b in range(NUM_BAYS):
        for i, (x, z) in enumerate(lower_seat_rows()):
            row = seats_in_row(x, z, b * BAY_WIDTH_Y + 0.9, (b + 1) * BAY_WIDTH_Y - 0.1)
            (red if 6 <= b < 11 else white).extend(s for s in row if not lower_seat_removed(s[1], i))
    place_seats(col_grandstand, "Krzeselka_Trybuna_Czerwone", seat_material("Mat_Krzeselka_Czerwone", (0.62, 0.07, 0.09)), red, empty_grandstand)
    place_seats(col_grandstand, "Krzeselka_Trybuna_Biale", seat_material("Mat_Krzeselka_Biale", (0.88, 0.88, 0.86)), white, empty_grandstand)

    print("--- 4. Generowanie 4 Masztów Oświetleniowych (3-nożne jupitery z odwróconym trapezem) ---")
    # Maszty wschodnie: cienie na ortofotomapie 2013 (NE Y≈+64, SE Y≈-59). Zachodnich nie widać
    # (cień trybuny głównej) — zostają w dotychczasowym, niezweryfikowanym położeniu (docs/zrodla.md).
    jupiters_cfg = [
        ("Jupiter_SW", (-68.0, -82.0, 0.0)),
        ("Jupiter_NW", (-68.0,  82.0, 0.0)),
        ("Jupiter_SE", ( 68.0, -61.5, 0.0)),
        ("Jupiter_NE", ( 68.0,  61.5, 0.0))
    ]
    
    for name, loc in jupiters_cfg:
        mast = build_floodlight_mast(col_jupiters, mats=mats, name=name, pitch_target=(0.0, 0.0), mast_pos=(loc[0], loc[1]))
        mast.location = loc

    print("--- 5. Generowanie Otoczenia (teren, al. Unii, tory, Atlas Arena, drzewa) ---")
    build_surroundings(col_surroundings, mats)

    # Zapis pliku roboczego .blend
    prepare_meshes_for_export()
    bake_ambient_occlusion()

    blend_path = os.path.join(ROOT, "stadion_lks_pelny.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Scena stadionu zapisana do: {blend_path}")

    # Surowy GLB do build/; `npm run model:optimize` kompresuje go (meshopt + WebP) do public/assets
    glb_dir = os.path.join(ROOT, "build")
    os.makedirs(glb_dir, exist_ok=True)
    glb_path = os.path.join(glb_dir, "estadio_da_gruz.raw.glb")

    print(f"Eksportowanie modelu GLB do: {glb_path} ...")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_gpu_instances=True
    )
    print(f"Pomyślnie wyeksportowano model GLB ({os.path.getsize(glb_path) / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    assemble_full_stadium()
