"""
Generowanie kompletnego stadionu ŁKS Łódź ("Estadio da Gruz", 1969-2012):
1. Trybuna Główna (Zachodnia) arch. Wyżnikiewicza i Szklarka:
   - 14 przęseł modułowych (108 m) z 15 kablobetonowymi dźwigarami
   - Brutalistyczne ukośne odciągi od strony al. Unii
   - Pawilon zaplecza z wstęgowymi oknami
   - Otwarta ku górze korona o realistycznej wysokości 14 m (bez dachu szczytowego)
   - Sektor dolny z niskim daszkiem blaszanym (sektor VIP / trybuna kryta z białą fasadą)
   - Słupki oświetleniowe wzdłuż szczytu korony
2. Korona Stadionu (Podkowa):
   - Murawa 105 x 68 m z bramkami piłkarskimi
   - Bieżnia żużlowa 400 m biegnąca w całości POMIĘDZY murawą a trybunami (nie zachodzi za Main Stand)
   - Sucha fosa betonowa okalająca całą bieżnię (1.8m x 1.4m)
   - Wały ziemne z 20 betonowymi stopniami
   - Historyczna tablica wyników z zegarem VIS A VIS Trybuny Głównej (na prostej wschodniej)
3. Cztery Maszty Oświetleniowe (Jupitery z 1970 r., h=46m):
   - Konstrukcja 3-nożna o przekroju trójkątnym zbieżnym ku górze
   - Głowica w kształcie ODWRÓCONEGO TRAPEZU (węższa podstawa na dole, szersza na górze)
   - 45 reflektorów pochylonych w dół o 28° w stronę murawy
4. Eksport do formatu GLB pod Three.js
"""

import bpy
import bmesh
import mathutils
import math
import sys
import os
import shutil

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.append(TOOLS_DIR)

from build_grandstand import create_materials, build_grandstand
from build_floodlight_mast import build_floodlight_mast
from build_horseshoe_bowl import (
    build_pitch_and_track,
    build_pitch_lines,
    build_moat_and_bowl,
    build_fan_banners,
    build_scoreboard
)

def build_goals_and_benches(col, mats):
    """Bramki piłkarskie i ławki rezerwowych."""
    POST_R = 0.06
    for sign_y in [-1, 1]:
        bm = bmesh.new()
        goal_y = sign_y * 52.5
        # Słupki pionowe
        for gx in [-3.66, 3.66]:
            p = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=POST_R, radius2=POST_R, depth=2.44)
            bmesh.ops.translate(bm, vec=(gx, goal_y, 1.22), verts=p['verts'])
        # Poprzeczka
        bar = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(7.32 + 2*POST_R, POST_R*2, POST_R*2), verts=bar['verts'])
        bmesh.ops.translate(bm, vec=(0.0, goal_y, 2.44), verts=bar['verts'])
        # Rama bramki (słupki i poprzeczka)
        mesh_frame = bpy.data.meshes.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Rama_Mesh")
        bm.normal_update()
        bm.to_mesh(mesh_frame)
        bm.free()
        obj_frame = bpy.data.objects.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Rama", mesh_frame)
        if mats and 'fascia' in mats:
            obj_frame.data.materials.append(mats['fascia'])
        col.objects.link(obj_frame)

        # Siatka za bramką (kratownica wireframe)
        bm_net = bmesh.new()
        back_y = goal_y + sign_y * 1.8
        v_net = [
            bm_net.verts.new((-3.66, goal_y, 2.44)),
            bm_net.verts.new(( 3.66, goal_y, 2.44)),
            bm_net.verts.new(( 3.66, back_y, 1.8)),
            bm_net.verts.new((-3.66, back_y, 1.8)),
            bm_net.verts.new((-3.66, back_y, 0.0)),
            bm_net.verts.new(( 3.66, back_y, 0.0)),
            bm_net.verts.new(( 3.66, goal_y, 0.0)),
            bm_net.verts.new((-3.66, goal_y, 0.0))
        ]
        bm_net.faces.new([v_net[0], v_net[1], v_net[2], v_net[3]]) # góra
        bm_net.faces.new([v_net[3], v_net[2], v_net[5], v_net[4]]) # tył
        bm_net.faces.new([v_net[0], v_net[3], v_net[4], v_net[7]]) # bok L
        bm_net.faces.new([v_net[1], v_net[6], v_net[5], v_net[2]]) # bok P
        
        mesh_net = bpy.data.meshes.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Siatka_Mesh")
        bm_net.normal_update()
        bm_net.to_mesh(mesh_net)
        bm_net.free()
        
        obj_net = bpy.data.objects.new(f"Bramka_{'N' if sign_y > 0 else 'S'}_Siatka", mesh_net)
        if mats and 'fascia' in mats:
            obj_net.data.materials.append(mats['fascia'])
        mod_net_wf = obj_net.modifiers.new("Siatka_Wireframe", 'WIREFRAME')
        mod_net_wf.thickness = 0.02
        mod_net_wf.use_replace = True
        col.objects.link(obj_net)
        obj_net.parent = obj_frame

    # Dwie ławki rezerwowych przy linii zachodniej (otwarte w stronę boiska +X)
    for sign_y in [-1, 1]:
        bm_b = bmesh.new()
        bx = -36.5
        by = sign_y * 14.0
        
        # Wiata (tył i dach)
        p_shelter = [
            (bx - 0.7, by - 3.5, 0.0),
            (bx - 0.7, by + 3.5, 0.0),
            (bx - 0.7, by + 3.5, 1.9),
            (bx - 0.7, by - 3.5, 1.9),
            (bx + 0.7, by - 3.5, 2.05),
            (bx + 0.7, by + 3.5, 2.05)
        ]
        vs = [bm_b.verts.new(p) for p in p_shelter]
        bm_b.faces.new([vs[0], vs[1], vs[2], vs[3]]) # ściana tylna
        bm_b.faces.new([vs[3], vs[2], vs[5], vs[4]]) # dach daszek
        
        # Siedziska wewnątrz wiaty
        for s in range(8):
            sy = by - 2.8 + s * 0.8
            seat = bmesh.ops.create_cube(bm_b, size=1.0)
            bmesh.ops.scale(bm_b, vec=(0.45, 0.45, 0.45), verts=seat['verts'])
            bmesh.ops.translate(bm_b, vec=(bx - 0.2, sy, 0.45), verts=seat['verts'])
            
        mesh_b = bpy.data.meshes.new(f"Lawka_Rezerwowych_{'N' if sign_y > 0 else 'S'}_Mesh")
        bm_b.normal_update()
        bm_b.to_mesh(mesh_b)
        bm_b.free()
        obj_b = bpy.data.objects.new(f"Lawka_Rezerwowych_{'N' if sign_y > 0 else 'S'}", mesh_b)
        if mats and 'roof_tin' in mats:
            obj_b.data.materials.append(mats['roof_tin'])
        col.objects.link(obj_b)


def assemble_full_stadium():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = create_materials()
    
    # Kolekcje główne
    root_col = bpy.data.collections.new("Estadio_da_Gruz_1969_2012")
    bpy.context.scene.collection.children.link(root_col)
    
    col_pitch = bpy.data.collections.new("01_Murawa_i_Bieznia")
    col_grandstand = bpy.data.collections.new("02_Trybuna_Glowna_Zachodnia")
    col_bowl = bpy.data.collections.new("03_Korona_Podkowa_Fosa")
    col_jupiters = bpy.data.collections.new("04_Jupitery_Maszty")
    
    for c in [col_pitch, col_grandstand, col_bowl, col_jupiters]:
        root_col.children.link(c)
        
    print("--- 1. Generowanie Murawy, Linii Boiska, Bieżni i Bramek ---")
    build_pitch_and_track(col_pitch, mats)
    build_pitch_lines(col_pitch, mats)
    build_goals_and_benches(col_pitch, mats)
    
    print("--- 2. Generowanie Korony (Wały, Fosa, Banery Kibicowskie, Zegar od Południa) ---")
    build_moat_and_bowl(col_bowl, mats)
    build_fan_banners(col_bowl, mats)
    build_scoreboard(col_bowl, mats)
    
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
    # Pozycjonowanie: czoło dolnych stopni (X_local = 0.0) styka się z fosą zachodnią przy X = -47.0m,
    # co gwarantuje, że bieżnia o szerokości 8m (od X = -37 do X = -45) i fosa (X = -45 do -46.8)
    # biegną w całości przed trybuną główną!
    empty_grandstand.location = (-47.0, 54.0, 0.0)

    print("--- 4. Generowanie 4 Masztów Oświetleniowych (3-nożne jupitery z odwróconym trapezem) ---")
    jupiters_cfg = [
        ("Jupiter_SW", (-68.0, -82.0, 0.0)),
        ("Jupiter_NW", (-68.0,  82.0, 0.0)),
        ("Jupiter_SE", ( 68.0, -82.0, 0.0)),
        ("Jupiter_NE", ( 68.0,  82.0, 0.0))
    ]
    
    for name, loc in jupiters_cfg:
        mast = build_floodlight_mast(col_jupiters, mats=mats, name=name, pitch_target=(0.0, 0.0), mast_pos=(loc[0], loc[1]))
        mast.location = loc

    # Zapis pliku roboczego .blend
    blend_path = "/home/mike/Projects/estadiodagruz/stadion_lks_pelny.blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Scena stadionu zapisana do: {blend_path}")

    # Eksport do formatu GLB (zoptymalizowany pod Three.js)
    glb_dir = "/home/mike/Projects/estadiodagruz/assets"
    os.makedirs(glb_dir, exist_ok=True)
    glb_path = os.path.join(glb_dir, "estadio_da_gruz.glb")
    
    print(f"Eksportowanie modelu GLB do: {glb_path} ...")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"Pomyślnie wyeksportowano model GLB ({os.path.getsize(glb_path) / 1024 / 1024:.2f} MB)")

    # Kopiujemy również bezpośrednio do folderu public/assets aplikacji Three.js
    pub_dir = "/home/mike/Projects/estadiodagruz/public/assets"
    os.makedirs(pub_dir, exist_ok=True)
    pub_glb = os.path.join(pub_dir, "estadio_da_gruz.glb")
    shutil.copyfile(glb_path, pub_glb)
    print(f"Zaktualizowano plik Three.js w: {pub_glb}")

if __name__ == "__main__":
    assemble_full_stadium()
