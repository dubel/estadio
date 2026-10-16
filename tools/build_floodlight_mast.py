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
    # 2. GŁOWICA W KSZTAŁCIE ODWRÓCONEGO TRAPEZU (KRÓTSZY BOK NA DOLE)
    # -------------------------------------------------------------------------
    bm_head = bmesh.new()
    
    W_BOT = 3.8   # krótsza podstawa trapezu na dole
    W_TOP = 7.4   # dłuższa podstawa trapezu na górze
    HEAD_H = 4.6  # wysokość platformy
    HEAD_D = 0.7  # grubość konstrukcji pomostu
    
    # Płyta czołowa odwróconego trapezu (w płaszczyźnie YZ, normalna w -X):
    front_pts = [
        (-HEAD_D / 2.0, -W_BOT / 2.0, -HEAD_H / 2.0),
        (-HEAD_D / 2.0,  W_BOT / 2.0, -HEAD_H / 2.0),
        (-HEAD_D / 2.0,  W_TOP / 2.0,  HEAD_H / 2.0),
        (-HEAD_D / 2.0, -W_TOP / 2.0,  HEAD_H / 2.0)
    ]
    f_verts = [bm_head.verts.new(p) for p in front_pts]
    bm_head.faces.new(f_verts)
    
    # Ekstruzja wzdłuż osi X o HEAD_D (w tył, tworząc bryłę platformy)
    ext = bmesh.ops.extrude_face_region(bm_head, geom=bm_head.faces[:])
    evs = [v for v in ext['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_head, vec=(HEAD_D, 0.0, 0.0), verts=evs)

    # Matryca reflektorów ułożona w trapez:
    # 6 rzędów reflektorów od dołu do góry, liczba reflektorów rośnie z szerokością trapezu
    row_counts = [5, 6, 7, 8, 9, 10] # od 5 lamp na dole do 10 lamp na górze
    lamp_r = 0.22
    
    for r_idx, count in enumerate(row_counts):
        t_row = (r_idx + 0.5) / len(row_counts)
        z_pos = -HEAD_H / 2.0 + t_row * HEAD_H
        row_w = (1.0 - t_row) * W_BOT + t_row * W_TOP - 0.6
        dy = row_w / count
        
        for c in range(count):
            y_pos = -row_w / 2.0 + (c + 0.5) * dy
            x_pos = -HEAD_D / 2.0 - 0.15 # wystaje przed platformę
            
            cone = bmesh.ops.create_cone(
                bm_head,
                cap_ends=True,
                segments=8,
                radius1=lamp_r,
                radius2=lamp_r * 0.75,
                depth=0.28
            )
            # obrót w stronę -X (kierunek świecenia)
            bmesh.ops.rotate(bm_head, cent=(0,0,0), matrix=mathutils.Matrix.Rotation(math.radians(90), 3, 'Y'), verts=cone['verts'])
            bmesh.ops.translate(bm_head, vec=(x_pos, y_pos, z_pos), verts=cone['verts'])

    # Pochylenie głowicy w dół (reflektory w -X pochylają się w stronę gruntu o -28°)
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
        obj_head.data.materials.append(mats['metal'])
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
