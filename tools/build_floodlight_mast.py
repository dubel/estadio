"""
Historyczny maszt oświetleniowy (Jupiter) stadionu ŁKS:
- Trzon kratownicowy o przekroju trójkątnym; poniżej 15 m trzy osobne nogi rozchodzące się do betonowych bloków.
- Dodatkowy pomost z reflektorami w połowie wysokości.
- Głowica w kształcie ODWRÓCONEGO TRAPEZU (krótszy bok na dole, dłuższy na górze).
- Reflektory pochylone w dół w stronę murawy.
"""

import bpy
import bmesh
import mathutils
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_floodlight_mast(col, mats=None, name="Jupiter", pitch_target=(0.0, 0.0), mast_pos=(0.0, 0.0)):
    """
    Tworzy trójnożny maszt z głowicą w kształcie odwróconego trapezu nakierowaną na pitch_target.
    Dwie przednie nogi zwrócone ku murawie, tylna noga odciągowa na zewnątrz stadionu.
    Głowica pochylona o 28° w dół w stronę murawy.
    """
    bm = bmesh.new()

    # Trzon: kratownica o przekroju trójkątnym od SPLIT_Z do szczytu. Poniżej trzy osobne nogi
    # (każda też kratownicowa) rozchodzą się do betonowych bloków fundamentowych
    # (punkt_swietlny_jupiter.png, widok_na_trybune_z_sektora_gosci.png).
    HEIGHT = 46.0
    SPLIT_Z = 15.0
    SHAFT_W, SHAFT_D = 2.2, 1.9     # przekrój trzonu w miejscu rozejścia nóg
    TOP_W, TOP_D = 1.4, 1.2
    BASE_W, BASE_D = 8.0, 7.0       # rozstaw stóp nóg
    FOOT_Z = 0.9                    # wierzch bloku fundamentowego
    SHAFT_TIERS, LEG_TIERS = 10, 5

    def corners(w, d, z):
        """Narożniki przekroju z czołem w kierunku -X: przód lewo, przód prawo, tył (odciąg)."""
        return [mathutils.Vector((-d / 3.0, -w / 2.0, z)), mathutils.Vector((-d / 3.0, w / 2.0, z)),
                mathutils.Vector((2.0 * d / 3.0, 0.0, z))]

    def lattice(tiers, decks=()):
        """Kratownica z kolejnych trójkątów przekroju: ściany z naprzemiennymi przekątnymi (Wireframe → pręty)."""
        rows = [[bm.verts.new(p) for p in tri] for tri in tiers]
        for i in range(1, len(rows)):
            prev, curr = rows[i - 1], rows[i]
            for side in range(3):
                nxt = (side + 1) % 3
                if (i + side) % 2 == 0:
                    bm.faces.new([prev[side], prev[nxt], curr[nxt]])
                    bm.faces.new([prev[side], curr[nxt], curr[side]])
                else:
                    bm.faces.new([prev[side], prev[nxt], curr[side]])
                    bm.faces.new([prev[nxt], curr[nxt], curr[side]])
        for i in decks:
            bm.faces.new(rows[i])

    def shaft_size(z):
        t = (z - SPLIT_Z) / (HEIGHT - SPLIT_Z)
        return (1.0 - t) * SHAFT_W + t * TOP_W, (1.0 - t) * SHAFT_D + t * TOP_D

    shaft = [corners(*shaft_size(SPLIT_Z + i * (HEIGHT - SPLIT_Z) / SHAFT_TIERS), SPLIT_Z + i * (HEIGHT - SPLIT_Z) / SHAFT_TIERS)
             for i in range(SHAFT_TIERS + 1)]
    lattice(shaft, decks=(0, 4, 7, SHAFT_TIERS))

    feet = corners(BASE_W, BASE_D, FOOT_Z)
    tops = shaft[0]
    for foot, top in zip(feet, tops):
        tiers = []
        for i in range(LEG_TIERS + 1):
            t = i / LEG_TIERS
            c = foot.lerp(top, t)
            r = (1.0 - t) * 0.45 + t * 0.12
            tiers.append([c + mathutils.Vector((r * math.cos(a), r * math.sin(a), 0.0))
                          for a in (0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0)])
        lattice(tiers)
    # Poziome stężenia między nogami
    for t in (0.35, 0.7):
        bm.faces.new([bm.verts.new(f.lerp(tp, t)) for f, tp in zip(feet, tops)])

    # Kąt obrotu masztu w stronę pitch_target
    dir_x = pitch_target[0] - mast_pos[0]
    dir_y = pitch_target[1] - mast_pos[1]
    yaw = math.atan2(dir_y, dir_x)
    # Czoło masztu i głowicy (-X) obracamy w stronę celu:
    rot_matrix = mathutils.Matrix.Rotation(yaw - math.pi, 3, 'Z')
    bmesh.ops.rotate(bm, cent=(0,0,0), matrix=rot_matrix, verts=bm.verts)

    mesh_tower = bpy.data.meshes.new(f"{name}_Wieza_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh_tower)
    bm.free()
    
    obj_tower = bpy.data.objects.new(f"{name}_Wieza", mesh_tower)
    col.objects.link(obj_tower)
    
    # Modyfikator Wireframe
    mod_wf = obj_tower.modifiers.new("Kratownica_Wireframe", 'WIREFRAME')
    mod_wf.thickness = 0.08
    mod_wf.use_boundary = True
    mod_wf.use_replace = True

    if mats and 'metal' in mats:
        obj_tower.data.materials.append(mats['metal'])

    # Betonowe bloki fundamentowe pod stopami nóg (do 0.3 m w gruncie)
    bm_f = bmesh.new()
    for foot in feet:
        c = bmesh.ops.create_cube(bm_f, size=1.0)
        bmesh.ops.scale(bm_f, vec=(1.6, 1.6, FOOT_Z + 0.3), verts=c['verts'])
        bmesh.ops.translate(bm_f, vec=(foot.x, foot.y, (FOOT_Z - 0.3) / 2.0), verts=c['verts'])
    bmesh.ops.rotate(bm_f, cent=(0, 0, 0), matrix=rot_matrix, verts=bm_f.verts)
    mesh_f = bpy.data.meshes.new(f"{name}_Fundamenty_Mesh")
    bm_f.normal_update()
    bm_f.to_mesh(mesh_f)
    bm_f.free()
    obj_f = bpy.data.objects.new(f"{name}_Fundamenty", mesh_f)
    if mats and 'concrete' in mats:
        obj_f.data.materials.append(mats['concrete'])
    col.objects.link(obj_f)
    obj_f.parent = obj_tower

    # Dodatkowe reflektory w połowie wysokości (punkt_swietlny_jupiter.png): pomost na czole trzonu,
    # 2 × 3 lampy pochylone ku murawie
    MID_Z = 25.0
    bm_m = bmesh.new()
    w_mid, d_mid = shaft_size(MID_Z)
    front_x = -d_mid / 3.0
    for (sx, sy, sz), (cx, cy, cz) in [((1.1, w_mid + 0.6, 0.08), (front_x - 0.55, 0.0, MID_Z - 0.45)),
                                       ((0.05, w_mid + 0.6, 0.9), (front_x - 1.08, 0.0, MID_Z + 0.0))]:
        c = bmesh.ops.create_cube(bm_m, size=1.0)
        bmesh.ops.scale(bm_m, vec=(sx, sy, sz), verts=c['verts'])
        bmesh.ops.translate(bm_m, vec=(cx, cy, cz), verts=c['verts'])
    lamp_rot = mathutils.Matrix.Rotation(math.radians(-20), 3, 'Y')
    for row, lz in enumerate((MID_Z + 0.65, MID_Z + 1.3)):
        for k in range(3):
            ly = (k - 1) * 0.72
            lamp = bmesh.ops.create_cube(bm_m, size=1.0)
            bmesh.ops.scale(bm_m, vec=(0.32, 0.64, 0.58), verts=lamp['verts'])
            bmesh.ops.rotate(bm_m, cent=(0, 0, 0), matrix=lamp_rot, verts=lamp['verts'])
            bmesh.ops.translate(bm_m, vec=(front_x - 0.5, ly, lz), verts=lamp['verts'])
            for f in {f for v in lamp['verts'] for f in v.link_faces}:
                f.normal_update()
                f.material_index = 1 if f.normal.x < -0.8 else 0
    bmesh.ops.rotate(bm_m, cent=(0, 0, 0), matrix=rot_matrix, verts=bm_m.verts)
    mesh_m = bpy.data.meshes.new(f"{name}_Reflektory_Srodek_Mesh")
    bm_m.normal_update()
    bm_m.to_mesh(mesh_m)
    bm_m.free()
    obj_m = bpy.data.objects.new(f"{name}_Reflektory_Srodek", mesh_m)
    if mats and 'metal' in mats:
        obj_m.data.materials.append(mats['metal'])
    if mats and 'lamp_glow' in mats:
        obj_m.data.materials.append(mats['lamp_glow'])
    col.objects.link(obj_m)
    obj_m.parent = obj_tower

    # -------------------------------------------------------------------------
    # 2. GŁOWICA W KSZTAŁCIE ODWRÓCONEGO TRAPEZU (6 POZIOMÓW ZGODNIE ZE ZDJĘCIEM)
    # -------------------------------------------------------------------------
    bm_head = bmesh.new()
    
    W_BOT = 3.6   # podstawa na dole (dla 3 lamp)
    W_TOP = 8.2   # podstawa na górze (dla 7 lamp)
    HEAD_H = 5.4  # wysokość rusztu
    HEAD_D = 0.85 # głębokość pomostów technicznych
    
    # 1. Płyta nośna / krata tylna trapezu
    front_pts = [
        (0.0, -W_BOT / 2.0, -HEAD_H / 2.0),
        (0.0,  W_BOT / 2.0, -HEAD_H / 2.0),
        (0.0,  W_TOP / 2.0,  HEAD_H / 2.0),
        (0.0, -W_TOP / 2.0,  HEAD_H / 2.0)
    ]
    f_verts = [bm_head.verts.new(p) for p in front_pts]
    bm_head.faces.new(f_verts)
    
    ext = bmesh.ops.extrude_face_region(bm_head, geom=bm_head.faces[:])
    evs = [v for v in ext['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_head, vec=(HEAD_D, 0.0, 0.0), verts=evs)

    # 2. 6 rzędów reflektorów w układzie ze zdjęcia (3, 4, 4, 5, 6, 7)
    row_counts = [3, 4, 4, 5, 6, 7]
    LAMP_W = 0.64
    LAMP_H = 0.58
    LAMP_D = 0.32
    
    for r_idx, count in enumerate(row_counts):
        t_row = r_idx / (len(row_counts) - 1)
        z_pos = -HEAD_H / 2.0 + (r_idx + 0.5) * (HEAD_H / len(row_counts))
        cur_w = (1.0 - t_row) * W_BOT + t_row * W_TOP
        
        # Pomost roboczy (barierka boczna i tylna)
        plat = bmesh.ops.create_cube(bm_head, size=1.0)
        bmesh.ops.scale(bm_head, vec=(HEAD_D, cur_w + 0.4, 0.08), verts=plat['verts'])
        bmesh.ops.translate(bm_head, vec=(HEAD_D / 2.0, 0.0, z_pos - LAMP_H / 2.0 - 0.05), verts=plat['verts'])
        
        # Barierki ochronne po bokach pomostu
        for side_sign in [-1, 1]:
            rail = bmesh.ops.create_cube(bm_head, size=1.0)
            bmesh.ops.scale(bm_head, vec=(HEAD_D + 0.3, 0.05, 0.75), verts=rail['verts'])
            bmesh.ops.translate(bm_head, vec=(HEAD_D / 2.0 - 0.1, side_sign * (cur_w / 2.0 + 0.15), z_pos), verts=rail['verts'])
            
        dy = (cur_w - 0.4) / count
        for c in range(count):
            y_pos = -(cur_w - 0.4) / 2.0 + (c + 0.5) * dy
            x_pos = -0.22 # przed ruszą
            
            # Skrzynka lampy
            lamp_box = bmesh.ops.create_cube(bm_head, size=1.0)
            bmesh.ops.scale(bm_head, vec=(LAMP_D, LAMP_W, LAMP_H), verts=lamp_box['verts'])
            bmesh.ops.translate(bm_head, vec=(x_pos, y_pos, z_pos), verts=lamp_box['verts'])
            
            # Czołowa szyba reflektora (oznaczona jako materiał index 1 - świecący)
            lamp_faces = {f for v in lamp_box['verts'] for f in v.link_faces}
            for f in lamp_faces:
                if f.normal.x < -0.8: # lico lampy skierowane w -X
                    f.material_index = 1
                else:
                    f.material_index = 0

    # 3. Czerwona lampa ostrzegawcza (przeszkodowa) na szczycie w osi
    z_top = HEAD_H / 2.0
    beacon = bmesh.ops.create_cone(
        bm_head,
        cap_ends=True,
        segments=12,
        radius1=0.18,
        radius2=0.16,
        depth=0.36
    )
    bmesh.ops.translate(bm_head, vec=(HEAD_D / 2.0, 0.0, z_top + 0.18), verts=beacon['verts'])
    for f in {f for v in beacon['verts'] for f in v.link_faces}:
        f.material_index = 2 # czerwone światło przeszkodowe

    # 4. Iglica odgromowa (odgromnik)
    needle = bmesh.ops.create_cone(
        bm_head,
        cap_ends=True,
        segments=8,
        radius1=0.03,
        radius2=0.005,
        depth=2.2
    )
    bmesh.ops.translate(bm_head, vec=(HEAD_D / 2.0, 0.0, z_top + 1.25), verts=needle['verts'])
    for f in {f for v in needle['verts'] for f in v.link_faces}:
        f.material_index = 0

    # 5. Ukośny wspornik kratownicowy łączący głowicę z masztem (pod spodem)
    bracket = bmesh.ops.create_cube(bm_head, size=1.0)
    bmesh.ops.scale(bm_head, vec=(HEAD_D * 1.1, W_BOT * 0.8, 1.2), verts=bracket['verts'])
    bmesh.ops.translate(bm_head, vec=(HEAD_D / 2.0, 0.0, -HEAD_H / 2.0 - 0.6), verts=bracket['verts'])
    for f in {f for v in bracket['verts'] for f in v.link_faces}:
        f.material_index = 0

    # Pochylenie głowicy w dół (reflektory w -X pochylają się ku murawie o -28°)
    bmesh.ops.rotate(bm_head, cent=(0,0,0), matrix=mathutils.Matrix.Rotation(math.radians(-28), 3, 'Y'), verts=bm_head.verts)
    
    # Obrót głowicy w poziomie tak, by wektor -X był skierowany na (dir_x, dir_y)
    bmesh.ops.rotate(bm_head, cent=(0,0,0), matrix=rot_matrix, verts=bm_head.verts)

    # Przesunięcie głowicy na szczyt masztu
    bmesh.ops.translate(bm_head, vec=(0.0, 0.0, HEIGHT + 2.2), verts=bm_head.verts)

    mesh_head = bpy.data.meshes.new(f"{name}_Glowica_Mesh")
    bm_head.normal_update()
    bm_head.to_mesh(mesh_head)
    bm_head.free()
    
    obj_head = bpy.data.objects.new(f"{name}_Glowica", mesh_head)
    if mats and 'metal' in mats:
        obj_head.data.materials.append(mats['metal'])        # index 0
    if mats and 'lamp_glow' in mats:
        obj_head.data.materials.append(mats['lamp_glow'])    # index 1
    if mats and 'lamp_beacon' in mats:
        obj_head.data.materials.append(mats['lamp_beacon'])  # index 2
        
    col.objects.link(obj_head)
    obj_head.parent = obj_tower
    return obj_tower

if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    col = bpy.data.collections.new("Test_Jupitery")
    bpy.context.scene.collection.children.link(col)
    
    mast = build_floodlight_mast(col, "Jupiter_SW", pitch_target=(0.0, 0.0), mast_pos=(-65.0, -80.0))
    mast.location = (-65.0, -80.0, 0.0)
    
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "jupiter_trapez_test.blend"))
    print("Zapisano test masztu trojnogiego z odwroconym trapezem.")
