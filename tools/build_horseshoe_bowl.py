"""
Generowanie korony stadionu (wały ziemne, podkowa), murawy, bieżni żużlowej,
betonowej fosy oraz historycznej tablicy świetlnej z zegarem.
"""

import bpy
import bmesh
import mathutils
import math

def build_pitch_and_track(col, mats):
    """Tworzy murawę oraz bieżnię lekkoatletyczną 400m."""
    PITCH_L = 105.0
    PITCH_W = 68.0
    
    # 1. Płyta murawy z pasami bocznymi (112m x 74m)
    bm_pitch = bmesh.new()
    bmesh.ops.create_grid(bm_pitch, x_segments=1, y_segments=1, size=1.0)
    bmesh.ops.scale(bm_pitch, vec=(74.0, 112.0, 1.0), verts=bm_pitch.verts)
    
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

    # 2. Bieżnia lekkoatletyczna (czerwono-grafitowy żużel)
    # Mieści się POMIĘDZY boiskiem a trybunami (zarówno podkową, jak i Trybuną Główną)
    STRAIGHT_L = 84.0
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
        
    mesh_track = bpy.data.meshes.new("Bieznia_Zuzlowa_Mesh")
    bm_track.normal_update()
    bm_track.to_mesh(mesh_track)
    bm_track.free()
    
    obj_track = bpy.data.objects.new("Bieznia_Zuzlowa", mesh_track)
    mat_cinder = bpy.data.materials.new("Mat_Cinder_Track")
    mat_cinder.use_nodes = True
    bsdf = mat_cinder.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.24, 0.18, 0.16, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.98
    obj_track.data.materials.append(mat_cinder)
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


def build_moat_and_bowl(col, mats):
    """
    Tworzy betonową fosę oraz podkowę trybun na wałach ziemnych.
    Fosa okala całą bieżnię (szerokość 1.8m, głębokość 1.4m).
    Podkowa wałów ziemnych biegnie od łuku południowego przez prostą wschodnią do łuku północnego.
    Strona zachodnia pozostaje wolna na Trybunę Główną.
    """
    STRAIGHT_L = 84.0
    R_TRACK_OUT = 45.0
    MOAT_W = 1.8
    MOAT_DEPTH = 1.4
    
    STAND_DEPTH = 22.0 # głębokość wału ziemnego
    STAND_H = 6.8      # realistyczna wysokość korony wału
    NUM_STEPS = 20     # 20 betonowych stopni
    
    bm_moat = bmesh.new()
    bm_bowl = bmesh.new()
    
    # 1. PEŁNA PĘTLA FOSY WOKÓŁ BIEŻNI
    # (Fosa biegnie również przed Trybuną Główną na zachodzie)
    NUM_FULL_SEGS = 72
    full_moat_path = []
    
    for i in range(NUM_FULL_SEGS):
        ang = 2.0 * math.pi * (i / NUM_FULL_SEGS)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cy = (STRAIGHT_L / 2.0) if sin_a > 0 else (-STRAIGHT_L / 2.0)
        px = R_TRACK_OUT * cos_a
        py = cy + R_TRACK_OUT * sin_a
        full_moat_path.append((px, py, cos_a, sin_a))
        
    moat_rings = []
    for px, py, nx, ny in full_moat_path:
        p0 = (px, py, 0.0)
        p1 = (px, py, -MOAT_DEPTH)
        p2 = (px + nx * MOAT_W, py + ny * MOAT_W, -MOAT_DEPTH)
        p3 = (px + nx * MOAT_W, py + ny * MOAT_W, 0.0)
        moat_rings.append([bm_moat.verts.new(p) for p in [p0, p1, p2, p3]])
        
    n_m = len(moat_rings)
    for i in range(n_m):
        next_i = (i + 1) % n_m
        rA = moat_rings[i]
        rB = moat_rings[next_i]
        for j in range(3):
            bm_moat.faces.new([rA[j], rB[j], rB[j+1], rA[j+1]])

    mesh_moat = bpy.data.meshes.new("Fosa_Betonowa_Mesh")
    bm_moat.normal_update()
    bm_moat.to_mesh(mesh_moat)
    bm_moat.free()
    obj_moat = bpy.data.objects.new("Fosa_Betonowa", mesh_moat)
    obj_moat.data.materials.append(mats['concrete_dark'])
    col.objects.link(obj_moat)

    # 2. PODKOWA TRYBUN (Łuk Południowy -> Prosta Wschodnia -> Łuk Północny)
    # Zostawia otwarty zachód (gdzie stoi Trybuna Główna o długości 108 m)
    # Kąt podkowy: od kąta w osi północno-zachodniej (155°) przez wschód (0°) do południowo-zachodniej (-155°)
    NUM_BOWL_SEGS = 56
    bowl_rings = []
    
    for i in range(NUM_BOWL_SEGS + 1):
        # Kąt od +152° (północ-zachód) przez wschód do -152° (południe-zachód)
        ang = math.radians(152.0 - (304.0 * (i / NUM_BOWL_SEGS)))
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        
        cy = (STRAIGHT_L / 2.0) if sin_a > 0 else (-STRAIGHT_L / 2.0)
        px = (R_TRACK_OUT + MOAT_W) * cos_a
        py = cy + (R_TRACK_OUT + MOAT_W) * sin_a
        nx = cos_a
        ny = sin_a
        
        # Stopnie na wale ziemnym
        b_pts = []
        cur_d = 0.0
        cur_z = 0.0
        step_d = STAND_DEPTH / NUM_STEPS
        step_h = STAND_H / NUM_STEPS
        
        b_pts.append((px, py, cur_z))
        for s in range(NUM_STEPS):
            cur_z += step_h
            b_pts.append((px + nx * cur_d, py + ny * cur_d, cur_z))
            cur_d += step_d
            b_pts.append((px + nx * cur_d, py + ny * cur_d, cur_z))
            
        # Tylna skarpa wału
        cur_d += 5.0
        b_pts.append((px + nx * cur_d, py + ny * cur_d, 0.0))
        
        bowl_rings.append([bm_bowl.verts.new(p) for p in b_pts])

    for i in range(len(bowl_rings) - 1):
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

    return obj_moat, obj_bowl


def build_fan_banners(col, mats):
    """
    Tworzy kibicowskie banery i historyczne graffiti wzdłuż prostej wschodniej ("Galera").
    """
    bm = bmesh.new()
    BX = 45.4
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
    build_moat_and_bowl(col, mats)
    build_scoreboard(col, mats)
    
    bpy.ops.wm.save_as_mainfile(filepath="/home/mike/Projects/estadiodagruz/bowl_v2_test.blend")
    print("Zapisano test korony z bieznią i zegarem vis a vis.")
