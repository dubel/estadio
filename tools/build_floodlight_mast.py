"""
Historyczny maszt oświetleniowy (Jupiter) stadionu ŁKS:
- Konstrukcja trójnożna (3 stalowe nogi kratownicowe) o przekroju trójkątnym zbieżnym ku górze.
- Głowica w kształcie ODWRÓCONEGO TRAPEZU (krótszy bok na dole, dłuższy na górze).
- Reflektory pochylone w dół w stronę murawy.
"""

import bpy
import bmesh
import mathutils
import math

def build_floodlight_mast(col, mats=None, name="Jupiter", pitch_target=(0.0, 0.0), mast_pos=(0.0, 0.0)):
    """
    Tworzy trójnożny maszt z głowicą w kształcie odwróconego trapezu nakierowaną na pitch_target.
    Dwie przednie nogi zwrócone ku murawie, tylna noga odciągowa na zewnątrz stadionu.
    Głowica pochylona o 28° w dół w stronę murawy.
    """
    bm = bmesh.new()
    
    HEIGHT = 46.0
    BASE_W = 5.2    # szerokość podstawy trójkąta (front)
    BASE_D = 4.5    # głębokość podstawy (odciąg tylny)
    TOP_W = 1.4
    TOP_D = 1.2
    NUM_TIERS = 12  # 12 poziomów stężeń
    TIER_H = HEIGHT / NUM_TIERS
    
    tier_verts = []
    
    for i in range(NUM_TIERS + 1):
        z = i * TIER_H
        t = i / NUM_TIERS
        w = (1.0 - t) * BASE_W + t * TOP_W
        d = (1.0 - t) * BASE_D + t * TOP_D
        
        # 3 narożniki przekroju trójkątnego z czołem w kierunku -X:
        # v0: przód lewo (-d/3, -w/2)
        # v1: przód prawo (-d/3, +w/2)
        # v2: tył odciąg (+2d/3, 0)
        v0 = bm.verts.new((-d / 3.0, -w / 2.0, z))
        v1 = bm.verts.new((-d / 3.0,  w / 2.0, z))
        v2 = bm.verts.new(( 2.0 * d / 3.0, 0.0, z))
        tier_verts.append([v0, v1, v2])
        
        # Tworzenie ścian trójkątnych na każdym poziomie
        if i > 0:
            prev = tier_verts[i - 1]
            curr = tier_verts[i]
            
            # 3 boki trójkąta:
            # Bok 0: v0-v1 (front)
            # Bok 1: v1-v2 (bok prawy)
            # Bok 2: v2-v0 (bok lewy)
            for side in range(3):
                next_side = (side + 1) % 3
                pA = prev[side]
                pB = prev[next_side]
                cA = curr[side]
                cB = curr[next_side]
                
                # Przekątna naprzemienna dla kratownicy
                if (i + side) % 2 == 0:
                    bm.faces.new([pA, pB, cB])
                    bm.faces.new([pA, cB, cA])
                else:
                    bm.faces.new([pA, pB, cA])
                    bm.faces.new([pB, cB, cA])

    # Pomosty poziome co 3 poziomy
    for i in [3, 6, 9, 12]:
        bm.faces.new(tier_verts[i])

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
    
    bpy.ops.wm.save_as_mainfile(filepath="/home/mike/Projects/estadiodagruz/jupiter_trapez_test.blend")
    print("Zapisano test masztu trojnogiego z odwroconym trapezem.")
