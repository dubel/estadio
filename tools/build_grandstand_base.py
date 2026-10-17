"""
Budowa podstawowego modułu Trybuny Głównej (Zachodniej) Stadionu ŁKS Łódź (1969-2012)
Projekt arch. Janusz Wyżnikiewicz, Jan Szklarek (1969/1972)
Skala: 1 jednostka = 1 metr (1:1)

Uruchomienie w Blenderze:
  1. W GUI: Wklej do okna 'Scripting' i kliknij 'Run Script'
  2. Z wiersza poleceń (CLI):
     blender -b --python tools/build_grandstand_base.py
"""

import bpy
import bmesh
import mathutils
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clear_scene():
    """Czyści scenę z domyślnych obiektów (kostka, światło, kamera)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_grandstand_module():
    # -------------------------------------------------------------------------
    # 1. PARAMETRY GEOMETRYCZNE I STRUKTURALNE (DANE WEJŚCIOWE)
    # -------------------------------------------------------------------------
    TOTAL_LENGTH_Y = 108.0      # Całkowita długość bazy trybuny w osi Y (metry)
    NUM_BAYS = 14               # Liczba powtarzalnych przęseł (taktów)
    BAY_WIDTH_Y = TOTAL_LENGTH_Y / NUM_BAYS  # Szerokość pojedynczego przęsła: 7.7142857 m
    
    BASE_WIDTH_X = 20.0         # Szerokość bazy pod trybuną w osi X (hala sportowa / rzut parteru)
    GIRDER_THICKNESS_Y = 0.50   # Grubość żelbetowego dźwigara nośnego w osi Y (50 cm)
    
    # Kąt nachylenia trybuny i wymiary stopni
    NUM_STEPS = 25              # Liczba rzędów/stopni w module
    STEP_DEPTH_X = BASE_WIDTH_X / NUM_STEPS  # Głębokość stopnia: 20.0 / 25 = 0.80 m
    # Kąt nachylenia trybuny ~30°: wznios całkowity = 20.0 * tan(30°) ≈ 11.547 m
    SLOPE_ANGLE_RAD = mathutils.Matrix.Rotation(0, 4, 'X') # kąt ok. 30 stopni
    TOTAL_HEIGHT_Z = 11.55      # Całkowity wznios stopni na długości 20m bazy
    STEP_HEIGHT_Z = TOTAL_HEIGHT_Z / NUM_STEPS # Wysokość stopnia: ~0.462 m
    
    # Rzędne wysokościowe (Z):
    Z_GROUND = 0.0              # Poziom murawy / posadzki hali
    Z_GIRDER_BASE = 0.0         # Poziom stopy fundamentowej dźwigara
    GIRDER_DEPTH_Z = 1.20       # Konstrukcyjna wysokość przekroju dźwigara pod stopniami
    
    # -------------------------------------------------------------------------
    # 2. UTWORZENIE KOLEKCJI DLA PROJEKTU
    # -------------------------------------------------------------------------
    col_name = "LKS_Trybuna_Glowna"
    if col_name in bpy.data.collections:
        col = bpy.data.collections[col_name]
    else:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)

    # -------------------------------------------------------------------------
    # 3. GENEROWANIE SIATKI POJEDYNCZEGO DŹWIGARA (GIRDER RIB)
    # -------------------------------------------------------------------------
    # Profil dźwigara w płaszczyźnie XZ:
    # Dolna podpora (X=0, Z=0) -> górny węzeł oparcia (X=20, Z=11.55)
    # Ze ściągiem i pasem dolnym tworzącym potężny profil nośny kablobetonu.
    girder_mesh = bpy.data.meshes.new("Dzwigar_Zelbetowy_Mesh")
    bm_girder = bmesh.new()

    # Wierzchołki profilu 2D (w płaszczyźnie XZ, przy Y=0):
    # P0: stopa dolna przód (fundament przy boisku)
    # P1: wierzch dolny (start stopni)
    # P2: wierzch górny (korona trybuny)
    # P3: tył górny (głowica węzła dachowo-ściennego)
    # P4: spód górnego podparcia na ścianie hali (X=20, Z=9.5)
    # P5: spód dolnego podparcia (X=0, Z=0)
    v_profile = [
        (0.0, 0.0, Z_GROUND),                         # 0: stopa przednia
        (0.0, 0.0, Z_GROUND + 0.6),                   # 1: start grzbietu
        (BASE_WIDTH_X, 0.0, TOTAL_HEIGHT_Z + 0.6),    # 2: szczyt grzbietu
        (BASE_WIDTH_X + 0.8, 0.0, TOTAL_HEIGHT_Z),    # 3: głowica tylna
        (BASE_WIDTH_X, 0.0, TOTAL_HEIGHT_Z - GIRDER_DEPTH_Z), # 4: pas dolny tył
        (0.8, 0.0, Z_GROUND)                          # 5: pas dolny przód
    ]
    
    bm_verts = [bm_girder.verts.new(p) for p in v_profile]
    bm_girder.faces.new(bm_verts)

    # Ekstruzja profilu wzdłuż osi Y o grubość dźwigara (GIRDER_THICKNESS_Y)
    extrude_result = bmesh.ops.extrude_face_region(bm_girder, geom=bm_girder.faces[:])
    extruded_verts = [v for v in extrude_result['geom'] if isinstance(v, bmesh.types.BMVert)]
    # Przesunięcie wyekstrudowanych wierzchołków w osi Y
    bmesh.ops.translate(bm_girder, vec=(0.0, GIRDER_THICKNESS_Y, 0.0), verts=extruded_verts)
    
    # Wycentrowanie dźwigara w osi Y przęsła: przesunięcie o (BAY_WIDTH_Y - GIRDER_THICKNESS_Y)/2 lub na osi 0
    # Umieszczamy dźwigar w osi przęsła Y=0 (od -GIRDER_THICKNESS_Y/2 do +GIRDER_THICKNESS_Y/2)
    bmesh.ops.translate(bm_girder, vec=(0.0, -GIRDER_THICKNESS_Y / 2.0, 0.0), verts=bm_girder.verts)
    
    bm_girder.normal_update()
    bm_girder.to_mesh(girder_mesh)
    bm_girder.free()

    obj_girder = bpy.data.objects.new("Dzwigar_Prefabrykowany", girder_mesh)
    col.objects.link(obj_girder)

    # -------------------------------------------------------------------------
    # 4. GENEROWANIE PŁASZCZYZNY SCHODKOWEJ STOPNI (TERRACE STEPS)
    # -------------------------------------------------------------------------
    # Schodki tworzą pełną szerokość przęsła (BAY_WIDTH_Y = 7.714 m) wzdłuż osi Y
    # i 25 rzędów po 0.80 m głębokości x 0.462 m wysokości w osiach X/Z.
    steps_mesh = bpy.data.meshes.new("Stopnie_Trybuny_Mesh")
    bm_steps = bmesh.new()

    # Tworzymy profil schodkowy (profil łamany w osi XZ):
    step_profile_pts = []
    cur_x = 0.0
    cur_z = Z_GROUND + 0.6  # oparcie na wierzchu dźwigara
    
    # Punkt startowy
    step_profile_pts.append((cur_x, 0.0, cur_z))
    
    for i in range(NUM_STEPS):
        # Podstopnica (pion w górę w osi Z)
        cur_z += STEP_HEIGHT_Z
        step_profile_pts.append((cur_x, 0.0, cur_z))
        
        # Stopnica (poziom w przód w osi X)
        cur_x += STEP_DEPTH_X
        step_profile_pts.append((cur_x, 0.0, cur_z))

    # Zamknięcie profilu od dołu (płyta korytkowa o grubości 15 cm)
    SLAB_THICKNESS = 0.15
    step_profile_pts.append((cur_x, 0.0, cur_z - SLAB_THICKNESS))
    step_profile_pts.append((0.0, 0.0, Z_GROUND + 0.6 - SLAB_THICKNESS))

    bm_step_verts = [bm_steps.verts.new(pt) for pt in step_profile_pts]
    bm_steps.faces.new(bm_step_verts)

    # Ekstruzja schodków na pełną szerokość przęsła (BAY_WIDTH_Y)
    ext_steps = bmesh.ops.extrude_face_region(bm_steps, geom=bm_steps.faces[:])
    ext_step_verts = [v for v in ext_steps['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_steps, vec=(0.0, BAY_WIDTH_Y, 0.0), verts=ext_step_verts)
    
    # Wyśrodkowanie w osi Y tak, by przęsło zaczynało się w Y=0 i kończyło w Y=BAY_WIDTH_Y
    # (lub symetrycznie względem osi dźwigara)
    # Ustawiamy: stopnie od Y=0 do Y=BAY_WIDTH_Y
    
    bm_steps.normal_update()
    bm_steps.to_mesh(steps_mesh)
    bm_steps.free()

    obj_steps = bpy.data.objects.new("Stopnie_Sektor_Przenslo", steps_mesh)
    col.objects.link(obj_steps)

    # -------------------------------------------------------------------------
    # 5. POŁĄCZENIE W MODUŁ I NAŁOŻENIE MODYFIKATORA ARRAY
    # -------------------------------------------------------------------------
    # Nakładamy modyfikator Array na oba obiekty (Dźwigar oraz Stopnie)
    # Używamy Constant Offset w osi Y o wartości BAY_WIDTH_Y (dokładnie 108.0 / 14 m)
    
    for obj in [obj_girder, obj_steps]:
        mod_array = obj.modifiers.new(name="Array_14_Przensel", type='ARRAY')
        mod_array.count = NUM_BAYS
        mod_array.use_relative_offset = False
        mod_array.use_constant_offset = True
        # Wektor przesunięcia: w osi X=0, w osi Y=BAY_WIDTH_Y (7.714m), w osi Z=0
        mod_array.constant_offset_displace = (0.0, BAY_WIDTH_Y, 0.0)

    # -------------------------------------------------------------------------
    # 6. DŹWIGAR ZAMYKAJĄCY (15. OŚ KONSTRUKCYJNA)
    # -------------------------------------------------------------------------
    # 14 przęseł wymaga 15 dźwigarów, aby zamknąć konstrukcję z obu stron trybuny.
    # Tworzymy kopię instancyjną (linked duplicate) dźwigara na pozycji Y = 14 * BAY_WIDTH_Y = 108.0m
    obj_girder_end = bpy.data.objects.new("Dzwigar_Zamykajacy_Os15", girder_mesh)
    obj_girder_end.location = (0.0, TOTAL_LENGTH_Y, 0.0)
    col.objects.link(obj_girder_end)

    print("=" * 60)
    print("TRYBUNA GŁÓWNA ŁKS - MODUŁ ZAINICJALIZOWANY POMYŚLNIE")
    print(f"Całkowita długość bazy (oś Y): {TOTAL_LENGTH_Y:.2f} m")
    print(f"Liczba przęseł: {NUM_BAYS}")
    print(f"Szerokość pojedynczego modułu: {BAY_WIDTH_Y:.4f} m ({TOTAL_LENGTH_Y}/{NUM_BAYS} m)")
    print(f"Szerokość bazy w rzucie (oś X): {BASE_WIDTH_X:.2f} m")
    print(f"Liczba rzędów w module: {NUM_STEPS} (głębokość: {STEP_DEPTH_X:.2f} m, wysokość: {STEP_HEIGHT_Z:.3f} m)")
    print("Modyfikatory Array skonfigurowane: 14 powtórzeń wzdłuż osi Y.")
    print("=" * 60)

if __name__ == "__main__":
    clear_scene()
    create_grandstand_module()
    # Zapis pliku roboczego .blend w celach weryfikacji i inspekcji
    blend_path = os.path.join(ROOT, "trybuna_glowna_baza.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Zapisano plik sceny: {blend_path}")
