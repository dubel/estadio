"""
Plastikowe krzesełka kubełkowe bez nóżek (stan ok. 2010–2012, widok_z_galery.jpg, krzesełka.png): czerwone
i białe na Galerze, w sektorze dolnym trybuny głównej czerwone pod czerwonym daszkiem i białe pod białymi.
Oparcie stoi tuż przed podstopniem rzędu wyżej (SEAT_BACK_GAP), siedzisko wysunięte nad stopień.

Każde krzesełko to osobny obiekt ze wspólną siatką, a cała grupa ma jednego rodzica (Empty) —
eksporter glTF zamienia taką grupę na jeden węzeł z EXT_mesh_gpu_instancing (InstancedMesh w Three.js).
Krzesełka nie biorą udziału w kolizjach (src/main.ts pomija InstancedMesh przy budowie Octree).
"""
import bmesh
import bpy

SEAT_PITCH = 0.5   # rozstaw krzesełek w rzędzie
SEAT_BACK_GAP = 0.3   # punkt mocowania od podstopnia rzędu wyżej: oparcie ok. 8 cm przed nim


# Profil kubełka (krzesełka.png): (x, z) linii środkowej od szczytu oparcia przez zaokrąglone przejście
# w siedzisko do wywiniętej krawędzi. Krzesełko patrzy w -X, (0, 0) to punkt mocowania na stopniu.
SEAT_PROFILE = [(0.20, 0.66), (0.18, 0.42), (0.13, 0.27), (0.03, 0.21), (-0.16, 0.24), (-0.26, 0.20)]
SEAT_HALF_W = (0.19, 0.21, 0.22, 0.22, 0.22, 0.22)    # połowa szerokości w punktach profilu
SEAT_WIDTH_SAMPLES = (-1.0, -1.0 / 3.0, 1.0 / 3.0, 1.0)
SEAT_BUCKET = 0.035                                   # podniesienie boków siedziska i wysunięcie boków oparcia


def _seat_mesh(name, mat):
    """
    Plastikowe krzesełko kubełkowe bez nóżek (krzesełka.png): zaokrąglony profil litery L — oparcie
    przechodzi łukiem w siedzisko, boki lekko podniesione jak w kubełku, krawędź siedziska wywinięta
    w dół. Cienka skorupa (materiał dwustronny) na niskim wsporniku przykręconym do betonu.
    Ok. 70 trójkątów: krzesełek jest kilka tysięcy.
    """
    bm = bmesh.new()
    rows = []
    for k, ((x, z), hw) in enumerate(zip(SEAT_PROFILE, SEAT_HALF_W)):
        row = []
        for w in SEAT_WIDTH_SAMPLES:
            dx = -SEAT_BUCKET * w * w if k < 3 else 0.0       # boki oparcia ku przodowi
            dz = SEAT_BUCKET * w * w if k >= 3 else 0.0       # boki siedziska w górę
            row.append(bm.verts.new((x + dx, w * hw, z + dz)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(len(SEAT_WIDTH_SAMPLES) - 1):
            f = bm.faces.new([r0[j], r0[j + 1], r1[j + 1], r1[j]])
            f.smooth = True
    c = bmesh.ops.create_cube(bm, size=1.0)                  # wspornik pod zgięciem
    bmesh.ops.scale(bm, vec=(0.12, 0.16, 0.2), verts=c['verts'])
    bmesh.ops.translate(bm, vec=(0.06, 0.0, 0.1), verts=c['verts'])
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    return mesh


def seat_material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.25          # lśniący plastik
    mat.use_backface_culling = False                       # skorupa kubełka widoczna z obu stron
    return mat


def place_seats(col, name, mat, positions, parent=None):
    """
    positions: (x, y, z) albo (x, y, z, obrót wokół Z) podstaw krzesełek w układzie rodzica.
    Bez obrotu krzesełko patrzy w -X. Zwraca Empty grupy.
    """
    root = bpy.data.objects.new(name, None)
    root.parent = parent
    col.objects.link(root)
    mesh = _seat_mesh(name + "_Mesh", mat)
    for i, pos in enumerate(positions):
        obj = bpy.data.objects.new(f"{name}_{i:05d}", mesh)
        obj.location = pos[:3]
        if len(pos) > 3:
            obj.rotation_euler = (0.0, 0.0, pos[3])
        obj.parent = root
        col.objects.link(obj)
    return root


def seats_in_row(x, z, y0, y1):
    """Krzesełka co SEAT_PITCH na odcinku [y0, y1] rzędu (x, z)."""
    n = int((y1 - y0) / SEAT_PITCH)
    off = (y1 - y0 - (n - 1) * SEAT_PITCH) / 2
    return [(x, y0 + off + k * SEAT_PITCH, z) for k in range(n)]
