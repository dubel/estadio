"""
Plastikowe krzesełka (stan ok. 2010–2012, widok_z_galery.jpg): czerwone na Galerze, w sektorze dolnym
trybuny głównej czerwone pod czerwonym daszkiem i białe pod białymi.

Każde krzesełko to osobny obiekt ze wspólną siatką, a cała grupa ma jednego rodzica (Empty) —
eksporter glTF zamienia taką grupę na jeden węzeł z EXT_mesh_gpu_instancing (InstancedMesh w Three.js).
Krzesełka nie biorą udziału w kolizjach (src/main.ts pomija InstancedMesh przy budowie Octree).
"""
import bmesh
import bpy

SEAT_PITCH = 0.5   # rozstaw krzesełek w rzędzie


def _seat_mesh(name, mat):
    """Krzesełko kubełkowe skierowane w -X (ku boisku): siedzisko, oparcie, wspornik."""
    bm = bmesh.new()
    for (x0, x1, y0, y1, z0, z1) in [(-0.20, 0.20, -0.21, 0.21, 0.36, 0.42),   # siedzisko
                                     (0.17, 0.23, -0.21, 0.21, 0.42, 0.80),    # oparcie
                                     (-0.06, 0.10, -0.04, 0.04, 0.0, 0.36)]:   # wspornik
        c = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=c['verts'])
        bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=c['verts'])
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
    bsdf.inputs['Roughness'].default_value = 0.45
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
